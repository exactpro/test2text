import streamlit as st

from test2text.services.db import get_db_client


def show_documentation():
    st.markdown("""
                    # Test2Text Application Documentation

                    ## About the Application
                
                    **Test2Text** is a tool for computing requirement's coverage by tests and generating relevant reports.  
                    The application provides a convenient interface for analysis the relationships between test cases and requirements.
                    
                """)
    st.divider()
    st.markdown("""
                    ## HOW TO USE
                    
                    ### Upload data
                    Click :gray-badge[:material/database_upload: Annotations] or :gray-badge[:material/database_upload: Requirements] to upload annotations and requirements from CSV files to the app's database.  
                    Then Annotations and Requirements are loaded and Test cases are linked to Annotations go to the next chapter.
                    
                    ### Renew data
                    Click :gray-badge[:material/cached: Controls] to transform missed and new texts into numeral vectors (embeddings).  
                    Update distances by embeddings for intelligent matching of Requirements and Annotations.  
                    After distances are refreshed (all Annotations linked with Requirement by distances) go to the next chapter.
                    
                    ### Generate reports
                    Click :gray-badge[:material/publish: Requirement's Report] or :gray-badge[:material/publish: Test cases Report] to make a report.  
                    Use filters and Smart search based on embeddings to select desired information.  
                    Analyze selected requirements or test cases by plotted distances.  
                    List of all requirements/test cases and their annotations are shown here.
                    
                    ### Visualize saved data 
                    Click :gray-badge[:material/dataset: Visualize vectors] to plot distances between vector representations of all requirements and annotations in multidimensional spaces.
                
                """)
    st.divider()
    with get_db_client() as db:
        st.markdown("""## Database overview""")
        table, row_count = st.columns(2)
        with table:
            st.write("Table name")
        with row_count:
            st.write("Number of entries")
        for table_name, count in db.get_db_full_info.items():
            with table:
                st.write(table_name)
            with row_count:
                st.write(count)
    st.divider()
    st.markdown("""    
                    ### Methodology
                    The application use a pre-trained transformer model from the [sentence-transformers library](https://huggingface.co/sentence-transformers), specifically [nomic-ai/nomic-embed-text-v1](https://huggingface.co/nomic-ai/nomic-embed-text-v1), a model trained to produce high-quality vector embeddings for text.  
                    The model returns, for each input text, a high-dimensional NumPy array (vector) of floating point numbers (the embedding).  
                    This arrays give a possibility to calculate Euclidian distances between test cases annotations and requirements to show how similar or dissimilar the two texts.  
                   """)

    st.markdown("""     
                    #### Euclidean (L2) Distance Formula
                    The Euclidean (L2) distance is a measure of the straight-line distance between two points (or vectors) in a multidimensional space.  
                    It is widely used to compute the similarity or dissimilarity between two vector representations, such as text embeddings.
                    """)
    st.markdown("""
                    Suppose we have two vectors:
                """)
    st.latex(r"""
                    \mathbf{a} = [a_1, a_2, ..., a_n] ,
            """)
    st.latex(r"""
                    \mathbf{b} = [b_1, b_2, ..., b_n] 
            """)

    st.markdown("""
                    The L2 distance between **a** and **b** is calculated as:
                """)

    st.latex(r"""
                    L_2(\mathbf{a}, \mathbf{b}) = \sqrt{(a_1 - b_1)^2 + (a_2 - b_2)^2 + \cdots + (a_n - b_n)^2}
    """)

    st.markdown("""
                    Or, more compactly:
    """)

    st.latex(r"""
                    L_2(\mathbf{a}, \mathbf{b}) = \sqrt{\sum_{i=1}^n (a_i - b_i)^2}
    """)

    st.markdown(""" 
                    - A **smaller L2 distance** means the vectors are more similar.  
                    - A **larger L2 distance** indicates greater dissimilarity.  
    """)

    st.markdown("""
                    This formula is commonly used for comparing the semantic similarity of embeddings generated from text using models like Sentence Transformers.
    """)
