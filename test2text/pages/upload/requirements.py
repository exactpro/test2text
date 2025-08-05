import streamlit as st


def show():
    st.title("Upload a file with requirements")

    uploaded_files = st.file_uploader("Choose a file with requirements", type="csv", accept_multiple_files=True)

    if not uploaded_files:
        st.info("Please upload a *.trace.csv file to extract rows.")
        return False
    
    from test2text.services.loaders.index_requirements import index_requirements_from_files
    index_requirements_from_files(uploaded_files)


if __name__ == "__main__":
    show()
