import streamlit as st

from components.navbar import render_navbar
from menus.aprovacoes import carregar

render_navbar()

carregar()