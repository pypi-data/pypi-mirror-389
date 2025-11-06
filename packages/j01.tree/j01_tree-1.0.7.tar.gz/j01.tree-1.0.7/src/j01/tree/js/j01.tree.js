//----------------------------------------------------------------------------
/** 
 * @fileoverview JSON supported unordered list based tree 
 * 
 * @author Roger Ineichen dev at projekt01 dot org.
 * @version Initial, not documented 
 */
//----------------------------------------------------------------------------
/* zrt-replace: "../j01TreeIMG" tal"string:${context/++resource++j01TreeIMG}" */

/* TODO: use metadata plugin for get/set the json loader uri */

//----------------------------------------------------------------------------
// public API
//----------------------------------------------------------------------------


(function($) {
$.fn.j01Tree = function (settings) {
    settings = $.extend({
        j01TreeCollapsedGif: '../j01TreeIMG/j01TreeCollapsed.gif',
        j01TreeExpandedGif: '../j01TreeIMG/j01TreeExpanded.gif',
        j01TreeStaticGif: '../j01TreeIMG/j01TreeStatic.gif',
        j01TreeCollapsedClass: 'j01TreeCollapsed',
        j01TreeExpandedClass: 'j01TreeExpanded',
        j01TreeStaticClass: 'j01TreeItem',
        j01TreeIconClass: 'j01TreeIcon',
        loadItemsMethodName: 'loadJSONTreeItems'
    }, settings);

    function j01TreeToggleItem(img) {
        ele = img.parentNode;
        var uri = $(img).attr('longDesc');
        if ($(ele).hasClass(settings.j01TreeExpandedClass)) {
            ele.className = settings.j01TreeCollapsedClass;
            $(img).attr("src", settings.j01TreeCollapsedGif);
        } else {
            hasChildren = $(ele).find('li').length;
            /* check for sub items */
            if (!hasChildren) {
                /* load childs from server via JSON */
                id = $(ele).attr('id');
                j01TreeLoadItems(uri, id);
            } else {
                ele.className = settings.j01TreeExpandedClass;
                $(img).attr("src", settings.j01TreeExpandedGif);
            }
        }
        return false;
    }

    function j01TreeLoadItems(uri, id) {
        /* each different json tree uses a own function for calling the childs */
        loader = settings.loadItemsMethodName;
        var jsonProxy = new JSONRPC(uri);
        jsonProxy.addMethod(loader, j01TreeAddItems, id);
        /* call the child loader method */
        var loaderMethod = jsonProxy[loader];
        loaderMethod(id);
    }

    function j01TreeAddItems(response, requestId) {
        var res = response['treeChilds'];
        var childs = res['childs'];
        if (childs.length) {
            ele = document.getElementById(res['id']);
            ele.className = settings.j01TreeExpandedClass;

            img = $(ele.firstChild);
            $(img).attr("src", settings.j01TreeExpandedGif);
            var ele = $(ele);
            var ul = null;

            /* find ul tag which will contain the new childs */
            var ul = ele.find('ul')[0]
            if (!ul){
                ele.append('<ul></ul>')
            }
            var ul = ele.find('ul')[0]

            /* render and append the new childs to the existing empty <ul> tag */
            for (var i=0; i<childs.length; i++) {
                var itemInfo = childs[i];
                var iconSrc = itemInfo['iconURL'];
                var hasChilds = itemInfo['hasChilds'];
                var linkHandler = itemInfo['linkHandler'];
                var contextURL = itemInfo['contextURL'];
                var aCSS = itemInfo['aCSS'];

                /* create toggle icon */
                if (iconSrc != '') {
                    var icon = $('<img></img>');
                    icon.attr("src", iconSrc);
                }
                /* create li tag */
                var li = $('<li></li>');
                li.attr("id", itemInfo['id']);

                /* create toggle image */
                var img = $('<img></img>');
                img.attr("width", "16");
                img.attr("height", "16");
                if (hasChilds) {
                    img.className = settings.j01TreeIconClass;
                    img.attr('longDesc', contextURL);
                    img.click(function(){
                        j01TreeToggleItem(this)
                    });
                    img.attr("src", settings.j01TreeCollapsedGif);
                    li.className = settings.j01TreeCollapsedClass;
                }
                else{
                    li.className = settings.j01TreeStaticClass;
                    img.attr("src", settings.j01TreeStaticGif);
                }
                /* create link or handler */
                var a = $('<a href=""></a>');
                if (linkHandler != '') {
                    a.click(eval(linkHandler));
                    a.attr("href", '#');
                }else {
                    a.attr("href", itemInfo['url']);
                }
                if (aCSS) {
                    a.addClass(aCSS);
                }
                /* append content to link */
                a.html(itemInfo['content']);
                li.append(a);
                /* append link to  to link */
                if (iconSrc != '') {
                    icon.insertBefore(a);
                    img.insertBefore(icon);
                }
                else {
                    img.insertBefore(a);
                }
                $(ul).append(li);
            }
        }
    }

    // render tree
    function renderTree(ul) {
        if ($(ul).length == 0) {
            return;
        }
        for (var i=0; i<ul.childNodes.length; i++) {
            var item = ul.childNodes[i];
            for (var si=0; si<item.childNodes.length; si++) {
                var subitem = item.childNodes[si];
                if (subitem.nodeName == "UL") {
                    renderTree(subitem, false);
                }
            }
            img = $(item.firstChild);
            img.click(function(){
                j01TreeToggleItem(this)
            });
        }
    }

    // initialize json trees
    return $(this).each(function(){
        renderTree(this);
    });
};
})(jQuery);
