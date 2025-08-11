import streamlit as st

def show_documentation():
    st.markdown("""
                    # Test2Text Application Documentation

                    ## About the Application
                
                    **Test2Text** is a tool for showing saved test cases, requirements, and annotations, as well as for generating reports and analyzing requirements coverage by tests. 
                    The application helps automate working with test requirements and provides a convenient interface for analyzing the relationships between test cases and requirements.
                
                    ---
                
                    ## Application Pages Overview
                
                    ### 1. **About application**
                    - **Description:** This page contains the user guide, a description of all pages, and instructions for working with the application.
                    - **How to use:** Simply read the description to understand the purpose of the application.

                    ### 2. **Annotations**
                    - **Description:** Work with annotations that link requirements and test cases.
                    - **How to use:**
                      - View existing annotations.
                      - Add new annotations to link requirements and test cases.
                    
                    ### 3. **Requirements**
                    - **Description:** View selected requirements.
                    - **How to use:**
                      - Browse the list of requirements.
                      - Add new requirements.
                      - Link requirements with annotations and test cases.
                    
                    ### 4. **Reports**
                    - **Description:** Generate reports on test cases, requirements, and their relationships.
                    - **How to use:**
                      - Select the desired report type (e.g., by test case or by requirement).
                      - Use filters to refine the report.
                      - Analyze selected requirements or test cases by showed and plotted distances.
                
                    ### 5. **Cache distances**
                    - **Description:** Update distances by embeddings (vector representations) for intelligent matching of requirements and annotations.
                    - **How to use:**
                      - Enter a search query or embedding.
                      - Get relevant results based on vector search.
                    
                    ### 6. **Visualize vectors**
                    - **Description:** Visualise distances by embeddings (vector representations) of requirements and annotations.
                    - **How to use:**
                      - Run script that will get all the data from database and will plot it to 2d and 3d graphics.
                    ---
                
                    ## Usage Tips
                    
                    - Upload annotations and requirements to the app's database. 
                    - Link test cases with requirements via annotations for better coverage analysis.
                    - Use filters and search for quick access to the information you need.
                    - Regularly review reports to monitor the quality of your tests.
                    - Refer to the "Documentation" page for help on using the application.
                
                """
    )