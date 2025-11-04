import yaml
import streamlit as st
import streamlit_canary as sc
from lk_utils import dedent

_state = sc.get_state(lambda: {
    'root': '',
    'search_paths': [],
    'entries': [],
    'export': {'source': '', 'target': ''}
}, version=3)


def main():
    st.set_page_config('Python Tree Shaking')
    st.title('Python Tree Shaking')
    # st.caption('Tree shaking Python dependencies.')

    root = sc.path_input('Input project root')
    if not root: return
    _state['root'] = root
    
    with st.expander('Add search paths', True):
        st.caption("What's this?", help=dedent(
            '''
            The "search paths" are similar to the `sys.path` concept in Python.
            Define one or more search paths here, from which the application
            will search for potentially imported libraries.

            Note: When a library with the same name both exists in two paths,
            one that appears first will be used. This is the same rule as
            `sys.path`.
            '''
        ))
        text = st.text_area(
            'Define search paths',
            placeholder=dedent(
                '''
                Input paths in YAML format.
                Paths can be absolute or relative to the project root as above.

                For example:
                
                - .venv/Lib/site-packages
                - .
                '''
            ),
            height=240
        )
        if text:
            _state['search_paths'] = yaml.safe_load(text)
    
    with st.expander('Add executable entries', True):
        st.caption("What's this?", help=dedent(
            '''
            Entries are entrance paths to ".py" scripts, which is executed by
            python interpreter.
            
            Usually these scripts contain `if __name__ == "__main__": ...` in
            their code.
            
            If your package is executed by `python -m <package>`, you should
            pass `<package>/__main__.py` here.
            
            If you have called `IPython`, `streamlit ...` (either in command
            line or by subprocess), you should also include them with
            `<site_packages>/IPython/__main__.py` and
            `<site_packages>/streamlit/__main__.py`.
            
            :yellow[Note: Entry must be under one of the search paths. If not,
            you need to add its parent folder to the search paths.]
            '''
        ))
        text = st.text_area(
            'Define entries',
            placeholder=dedent(
                '''
                Input paths in YAML format.
                Paths can be absolute or relative to the project root as above.

                For example:
                
                - .venv/Lib/site-packages/IPython/__main__.py
                - src/hello_world/__main__.py
                - run.py
                '''
            ),
            height=240
        )
        if text:
            _state['entries'] = yaml.safe_load(text)
    
    with st.expander('Tree shaking and export', True):
        if not _state['search_paths']:
            st.warning(
                'This section is not available. You need to complete '
                '"Add search paths" section first.'
            )
            return
        
        x = st.radio(
            'Select ONE or ALL as dependency source',
            ['ALL'] + _state['search_paths'],
            index=1
        )
        _state['export']['source'] = '' if x == 'ALL' else x
        
        _state['export']['target'] = sc.path_input(
            'Output path',
            '{}/minideps'.format(root),
            help=dedent(
                '''
                If target path not exists, will create it.
                
                If target path exists but empty, will use it.
                
                If target path exists and not empty, will do incremental updates
                to it.
                '''
            )
        )
    
    with st.container(horizontal=True):
        if st.button('Minify dependency tree', type='primary'):
            print(_state, ':v2l')
        if st.button('Save as config file'):
            # TODO: popup a dialog to choose save path.
            pass


if __name__ == '__main__':
    main()
