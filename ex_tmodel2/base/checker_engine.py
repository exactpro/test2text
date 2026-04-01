from typing import Sequence

from ex_tmodel2.base.converters.base_protocol_converter import BaseProtocolConverter
from ex_tmodel2.base.soup import State, MessageReader, StateUpdater, TransactionSplitter, RuleCheck, \
    ProblemCollector, ErrorCheck


class CheckerEngine:
    def __init__(self,
                 protocol_list: list[str],
                 output_data_folder: str,
                 states: Sequence[State],
                 message_reader: MessageReader,
                 converters: Sequence[BaseProtocolConverter],
                 state_updaters: Sequence[StateUpdater],
                 transaction_splitter: TransactionSplitter,
                 rule_checks: Sequence[RuleCheck],
                 problem_collector: ProblemCollector,
                 ):
        self._states: list[State] = list(states)
        self._message_reader: MessageReader = message_reader
        self._converters: list[BaseProtocolConverter] = list(converters)
        self._state_updaters: list[StateUpdater] = list(state_updaters)
        self._transaction_splitter: TransactionSplitter = transaction_splitter
        self._rule_checks: list[RuleCheck] = list(rule_checks)
        self._problem_collector: ProblemCollector = problem_collector

        self.protocol_list = protocol_list
        self.output_data_folder = output_data_folder

        # self.protocol_parsers = ProtocolParsers()
        # self.tx_assembler = TransactionAssembler()
        # file_protocols = find_jsons(self.output_data_folder, protocol_list=self.protocol_list)
        # reader = merge_jsonl_with_protocol(file_protocols)

    def run(self):
        transactions_iter = self._transaction_splitter.split(
            self._message_reader,
            self._converters,
        )

        for transaction in transactions_iter:
            previous_states: Sequence[State] = tuple(self._states)

            for state in self._states:
                transaction.state_snapshots[state.name] = state.save()

            for updater in self._state_updaters:
                for state in self._states:
                    if updater.supports(state):
                        updater.update(state, transaction)

            current_states: Sequence[State] = tuple(self._states)

            errors_for_transaction: list[ErrorCheck] = []
            for rule in self._rule_checks:
                rule_errors = rule.check(transaction, previous_states, current_states)
                if rule_errors:
                    errors_for_transaction.extend(rule_errors)

            if errors_for_transaction:
                self._problem_collector.collect(errors_for_transaction)
