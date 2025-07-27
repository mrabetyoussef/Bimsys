COSTUM_LOADER = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        <div id="loader">
            <h1>BIMSYS</h1>
            <div class="spinner"></div>
        </div>

        {%app_entry%}

        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''
