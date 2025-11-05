import streamlit as st
from streamlit_ace import st_ace

from pp3d.playground import i18n


def code_editor(
    value: str, language: str = "python", height: int = 480, theme: str = "dracula", font_size: int = 14
) -> str:
    """Create a code editor widget in Streamlit.

    Args:
        value (str): The initial value of the editor.
        language (str): The programming language for syntax highlighting. Defaults to "python".
        height (int): The height of the editor. Defaults to 480.
        theme (str): The theme of the editor. Defaults to "dracula".
        font_size (int): The font size of the editor. Defaults to 14.

    Returns:
        str: The code written in the editor.
    """
    return st_ace(value=value, language=language, height=height, theme=theme, font_size=font_size)


def select_language() -> str:
    """
    Create a language selection widget in Streamlit.

    Returns:
        str: The selected language.
    """
    return st.selectbox(
        label="Select Language",
        label_visibility="hidden",
        options=list(i18n.translation.keys()),
        format_func=lambda selected: i18n.language_names[selected],
    )


def select_algorithm() -> str:
    """
    Create an algorithm selection widget in Streamlit.

    Returns:
        str: The selected algorithm.
    """
    return st.selectbox(
        label=i18n.translate("select_algorithm"),
        options=list(i18n.algorithm_names.keys()),
        format_func=lambda selected: i18n.algorithm_names[selected][st.session_state.selected_language],
    )
