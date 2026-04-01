from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import List, Callable, Iterator, Union, Optional
import importlib
import inspect
import logging
import pkgutil
import sys
from types import ModuleType
from typing import Iterable, Type, Any
from ex_tmodel2.base.base import StateTransition, State, TransitionAudit

# Module logger
logger = logging.getLogger(__name__)


def setup_rule_logging(
    level: int = logging.INFO,
    log_file: str | None = None,
    error_log_file: str | None = None,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    file_mode: str = "a"
) -> None:
    """
    Configure logging for the rule runner with separate error output.

    - All messages go to stdout (or log_file if specified)
    - WARNING and above also go to stderr (or error_log_file if specified)

    :param level: Minimum log level (default: INFO)
    :param log_file: Optional file path for all output (includes errors)
    :param error_log_file: Optional file path for errors only (WARNING and above)
    :param log_format: Log message format
    :param file_mode: File open mode - "a" to append (default), "w" to overwrite
    """
    formatter = logging.Formatter(log_format)

    # Handler for all messages -> stdout or file
    if log_file:
        main_handler = logging.FileHandler(log_file, mode=file_mode)
    else:
        main_handler = logging.StreamHandler(sys.stdout)
    main_handler.setLevel(level)
    main_handler.setFormatter(formatter)

    # Handler for WARNING and above -> stderr or file
    if error_log_file:
        error_handler = logging.FileHandler(error_log_file, mode=file_mode)
    else:
        error_handler = logging.StreamHandler(sys.stderr)
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(formatter)

    # Configure the module logger
    logger.setLevel(level)
    logger.addHandler(main_handler)
    logger.addHandler(error_handler)


def rule_check(
    rule_description: str,
    rule_tags: list[str] | tuple[str, ...],
) -> Callable[[Type[Any]], Type[Any]]:
    """
    Class decorator that attaches rule metadata to the class.
    """
    # Normalize tags to an immutable tuple
    norm_tags = tuple(rule_tags)

    def decorator(cls: Type[Any]) -> Type[Any]:
        # Attach metadata in a single namespace to avoid clutter
        setattr(cls, "__rule_metadata__", {
            "rule_description": rule_description,
            "rule_tags": norm_tags,
        })
        # Convenience aliases if you want
        cls.rule_description = rule_description
        cls.rule_tags = norm_tags
        return cls

    return decorator


@dataclass
class ReportedRuleData:
    id: str
    testcase: str
    annotation: str
    status: bool
    description: str
    file: str
    line: int
    rule_description: str = ""
    rule_tags: tuple[str, ...] = ()

def report_print_text(description) -> ReportedRuleData:
    return ReportedRuleData(
        "",
        "",
        "",
        True,
        description,
        "",
        0
    )

def report_rule_for_state_transition(transition: StateTransition, annotation, status, description="", id="", testcase=None) -> ReportedRuleData:
    frame_info = sys._getframe(1)
    frame_filename = frame_info.f_code.co_filename
    frame_line_number = frame_info.f_lineno

    return ReportedRuleData(
        id,
        testcase if testcase else transition.input_signal.signal_testcase,
        annotation,
        status,
        description,
        frame_filename,
        frame_line_number
    )

class NoRelevantCheckClass:
    def __init__(self):
        ...


no_relevant = NoRelevantCheckClass()

class RuleCheck:

    @abstractmethod
    def check(
        self,
        old_state: State,
        transition: StateTransition,
        new_state: State,
        audit_data: TransitionAudit
    ) -> Iterator[ReportedRuleData] | NoRelevantCheckClass:
        """Run rule checks and return list of found problems. If this check is not relevant for this Transition return no_relevant
        If no problem found return empty list. The engine assumes that if problem list is empty that this check was relevant
        in this situation and no problem was found. Also it adds this ruleID in list of checked tests.
        """
        raise NotImplementedError

    def report_rule(self, transition: StateTransition, annotation, status, description="", id="", testcase=None) -> ReportedRuleData:
        frame_info = sys._getframe(1)
        frame_filename = frame_info.f_code.co_filename
        frame_line_number = frame_info.f_lineno

        return ReportedRuleData(
            id,
            testcase if testcase else transition.input_signal.signal_testcase,
            annotation,
            status,
            description,
            frame_filename,
            frame_line_number,
            rule_description=self.rule_description,
            rule_tags=self.rule_tags
        )


class RuleRunner:

    VERBOSE: bool = False

    @staticmethod
    def is_verbose() -> bool:
        return RuleRunner.VERBOSE

    def __init__(self, package_names: list[str], exclude: list[str] = None, verbose: bool = False):
        """

        :param package_names:
        :param exclude: It possible to enlist packages/modules/individual checks in module just use "." separator
        :param verbose: Enable verbose output for rules
        """
        self.package_names = package_names
        self.rule_checks: list[RuleCheck] = []
        self.exclude = exclude
        RuleRunner.VERBOSE = verbose

    @staticmethod
    def __iter_modules_in_package(package_name: str) -> Iterable[ModuleType]:
        """Yield all modules in a package (recursively)."""

        try:
            package = importlib.import_module(package_name)
        except ModuleNotFoundError as e:
            # Module does not exist or cannot be found on sys.path
            logger.error("Module not found: %s", e.name)
            return
        except ImportError as e:
            # Found something, but import failed for another reason
            logger.error("Import error: %s", e)
            return

        package = importlib.import_module(package_name)
        if not hasattr(package, "__path__"):
            # Not a package, just a single module
            yield package
            return

        # Include the package itself
        yield package

        for _, mod_name, is_pkg in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
            try:
                module = importlib.import_module(mod_name)
            except ImportError:
                continue
            yield module

    def __find_annotated_classes(self, tags: list[str] | None = None) -> list[Type[Any]]:
        """
        Scan given packages and return classes that have a specific annotation.

        - annotation_attr: attribute name set by your decorator/annotation
          (e.g. '_my_marker', '__my_annotation__', etc.)
        - annotation_value: if not None, require that getattr(cls, annotation_attr) == annotation_value
        """
        result: list[Type[Any]] = []

        for pkg_name in self.package_names:
            for module in self.__iter_modules_in_package(pkg_name):
                for member_name, obj in inspect.getmembers(module, inspect.isclass):
                    # Ensure the class is defined in this module, not just imported
                    if obj.__module__ != module.__name__:
                        continue

                    if not hasattr(obj, "__rule_metadata__"):
                        continue

                    full_name = obj.__module__ + "." + member_name
                    if (self.exclude is not None) and (any(full_name.startswith(s) for s in self.exclude)):
                        continue

                    #FIXME There is need to specify for example some tags
                    #if tags is not None:
                        #if getattr(obj, "__rule_metadata__.tags", None) != annotation_value:
                        #    continue

                    result.append(obj)

        return result

    def customise_rule_names_func(self, annotation: str, new_state: State) -> str:
        return annotation

    def create_checks(self) -> list[str]:
        annotated = self.__find_annotated_classes()

        result: list[str] = []
        for cls in annotated:
            try:
                instance_check = cls()
                self.rule_checks.append(instance_check)
                result.append(f"{cls.__module__}.{cls.__name__}")
            except TypeError as e:
                logger.error("Could not create instance of check %s: %s", cls, e)

        return result

    def run_checks(self, old_state: State, transition: StateTransition, new_state: State,
            audit_data: TransitionAudit) \
            -> dict[str, list[ReportedRuleData] | NoRelevantCheckClass]:

        result: dict[str, list[ReportedRuleData] | NoRelevantCheckClass] = {}

        for rule_check_instance in self.rule_checks:

            try:
                check_result_generator = rule_check_instance.check(old_state, transition, new_state, audit_data)

                if isinstance(check_result_generator, Iterable):

                    check_list_data = []
                    no_relevant_check = False
                    cont = True
                    while cont:
                        try:
                            # Get the next yielded value
                            value = next(check_result_generator)

                            if self.customise_rule_names_func is not None:
                                value.annotation = self.customise_rule_names_func(value.annotation, new_state)

                            check_list_data.append(value)

                        except StopIteration as e:
                            if isinstance(e.value, NoRelevantCheckClass):
                                no_relevant_check = True
                            cont = False

                    if not no_relevant_check:
                        result[rule_check_instance.__class__.__name__] = check_list_data
                elif isinstance(check_result_generator, NoRelevantCheckClass):
                    pass
                else:
                    logger.warning("Strange return value from %s: %s",
                                   rule_check_instance.__class__.__name__, check_result_generator)

            except Exception as e:
                logger.error("Running check %s failed with exception",
                             rule_check_instance.__class__.__name__, exc_info=True)

                result[rule_check_instance.__class__.__name__] = [
                    report_rule_for_state_transition(transition,
            f"[EXCEPTION] {e}",
                        False
                    )
                ]

        return result

