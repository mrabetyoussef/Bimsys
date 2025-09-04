var dagcomponentfuncs = (window.dashAgGridComponentFunctions =
    window.dashAgGridComponentFunctions || {});

dagcomponentfuncs.StockLink = function (props) {
    if (!props.value) return null;

    // extraire avant le " - "
    var id = props.value.split(" - ")[0].trim();

    return React.createElement(
        "a",
        { href: "/BIMSYS/task/" + id },
        props.value // affichage complet : "123 - Faire le modèle"
    );
};
