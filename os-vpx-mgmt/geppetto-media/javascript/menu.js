var menu_backgroundHiliteClass			= "menu_item_text_hover";
var menu_backgroundNotHiliteClass		= "menu_item_text";
var menu_background2HiliteClass			= "menu_submenu_icon_hover";
var menu_background2NotHiliteClass		= "menu_submenu_icon";
var menu_borderHiliteClass			    = "menu_border_hilite";
var menu_borderNotHiliteClass			= "menu_border";

var onWindowsIE = (navigator.appVersion.indexOf("MSIE") != -1 &&
				navigator.appVersion.indexOf("Windows") != -1);

// Menu scripts
var visibleSubMenu 		= null;
var subMenuToShow		= null;
var subMenuToHide		= null;
var reenterMenuCount	= 0;
var submenu_shadows 	= new Array

function menuFindParentCell(el)
{
	var curEl = el;
	while (curEl != null && curEl.className != "menu_item")
		curEl = curEl.parentElement;
	return curEl;
}

function setTableCellClass(tbl, row, col, cssClass)
{
    if(tbl.tBodies[0].rows !=null && tbl.tBodies[0].rows[row] !=null )
        {
            cell = tbl.tBodies[0].rows[row].cells[col];
            if (cell != null)
                cell.className = cssClass;
        }
}

function menu_onfocus(el)
{
	menu_onmouseover(el);
}

function menu_onblur(el)
{
	menu_onmouseout(el);
}

function menu_onmouseover(el)
{
	var menuCell = menuFindParentCell(el);
	if (menuCell == null)
		return;
	
	setTableCellClass(menuCell, 0, 0, menu_borderHiliteClass);
	setTableCellClass(menuCell, 1, 0, menu_borderHiliteClass);
	setTableCellClass(menuCell, 1, 3, menu_borderHiliteClass);
	setTableCellClass(menuCell, 2, 0, menu_borderHiliteClass);

	setTableCellClass(menuCell, 1, 1, menu_backgroundHiliteClass);
	setTableCellClass(menuCell, 1, 2, menu_background2HiliteClass);
}

function menu_onmouseout(el)
{
	var menuCell = menuFindParentCell(el);
	if (menuCell == null)
		return;

	setTableCellClass(menuCell, 0, 0, menu_borderNotHiliteClass);
	setTableCellClass(menuCell, 1, 0, menu_borderNotHiliteClass);
	setTableCellClass(menuCell, 1, 3, menu_borderNotHiliteClass);
	setTableCellClass(menuCell, 2, 0, menu_borderNotHiliteClass);

	setTableCellClass(menuCell, 1, 1, menu_backgroundNotHiliteClass);
	setTableCellClass(menuCell, 1, 2, menu_background2NotHiliteClass);
}

function menu_onclick(el, href, openInNewWindow)
{
	var menuCell = menuFindParentCell(el);

	if (menuCell == null)
		return;

	if (href != null)
	{
		// Is the user holding down the shift key?
		if (openInNewWindow || window.event.shiftKey)
			window.open(href);
		else
			window.location = href;
	}
}

function submenu_calcMenuTop(subMenu, menuID, parent)
{
	var curEl = subMenu;
	var topVal = 0;
    topVal += subMenu.offsetHeight;
	while (curEl != null)
	{
		topVal += curEl.offsetTop;
		curEl = curEl.offsetParent; // looks like ie6 recurses but firefox null!
	}
	
	var newMenu = document.getElementById(menuID);
	if (newMenu != null)
	{
		var docTop = 0;
		var screenHeight = 0;
		// ie
		if (document.all != null)
		{
			if (document.documentElement.clientHeight != null)
			{
				docTop = document.documentElement.scrollTop;
				screenHeight = document.documentElement.clientHeight;
			}
			else
			{
				docTop = document.body.scrollTop;
				screenHeight = document.body.clientHeight;
			}
		}
		// netscape or mozilla
		else
		{
			docTop = window.pageYOffset;
				screenHeight = window.innerHeight;
		}
			
		if (topVal - docTop + newMenu.offsetHeight > screenHeight)
			topVal -= newMenu.offsetHeight - 21;

		if (topVal < docTop)
			topVal = docTop - 2;
	}
	
	return topVal - parent.offsetTop;
}

function submenu_calcMenuLeft(subMenu, parent)
{
	var curEl = subMenu;
	var leftVal = 0;
	while (curEl != null)
	{
        leftVal += curEl.offsetLeft;
	    curEl = curEl.offsetParent;
	}
        
	return leftVal - parent.offsetLeft;
}

function submenu_keypressopen(el, menuID, parentId)
{
	// if the key is left arrow, open the menu
	if (window.event.keyCode == 39)
	{
		var containingTable = el.offsetParent.offsetParent;
		if (containingTable != null)
		{
			submenu_onmouseover(containingTable, menuID, parentId);
			containingTable.focus;
		}
	}
}

function submenu_tabfocusin(el, menuID)
{
	menu_onmouseover(el);
}

function submenu_tabfocusout(el, menuID)
{
	var focusEl = document.activeElement;
	var containingTable = el.offsetParent.offsetParent;
	if (containingTable != null)
		submenu_onmouseout(containingTable, menuID);
}

function submenu_adjustDimensions(subMenu)
{
	maxHeight = parseInt(subMenu.style.customHeight);
	maxWidth  = parseInt(subMenu.style.customWidth);
	bHorScroll  = (subMenu.style.customScroll == "XScroll" || subMenu.style.customScroll == "XYScroll") ? true : false;
	bVerScroll  = (subMenu.style.customScroll == "YScroll" || subMenu.style.customScroll == "XYScroll") ? true : false;

	hScrollAdded = false;

	if (maxWidth > 0)
	{
		if (bHorScroll)
		{
			// see if we need to validate the maximum width requirements
			if (maxWidth > 0)
			{
				if (subMenu.offsetWidth > maxWidth)
				{
					subMenu.style.width = maxWidth + "px";
					subMenu.style.overflowX = "auto";
	
					// adjust maxWidth with the new value of offsetWidth
					// This is required, so that we don't enter this function
					// as offsetWidth will always be a bit higher than maxWidth
					subMenu.style.customWidth = subMenu.offsetWidth;
	
					// add the scroll bar height to current size, because
					// otherwise in extreme case, when there is only one VM
					// and it has very long name, the horizontal scroll bar
					// will hide its name.
					subMenu.style.height = subMenu.offsetHeight + 16; // 16 is approximate height of scroll bar
	
					// So that we know we added a horizontal scroll bar
					hScrollAdded = true;
				}
			}
		}
		else
		{
            subMenu.style.width = (maxWidth + "px");
			subMenu.style.overflowX = "hidden";
		}
	}

	if (maxHeight > 0)		
	{
		if (bVerScroll)
		{
			// Now verify that we haven't exceeded maximum height
			if (subMenu.offsetHeight > maxHeight)
			{
				subMenu.style.height = maxHeight  + "px";
				subMenu.style.overflowY = "auto";
				
				// adjust the height so that we don't enter this path again
				// unless the page is refreshed
				subMenu.style.customHeight = subMenu.offsetHeight;

				// if we didn't add a horizontal scroll bar, that there may be
				// a case when all the VM are only one letter name, and in that
				// case, the scroll bar will hide their names, so we need to increase
				// the width
				if (hScrollAdded == false)
				{
					subMenu.style.width = subMenu.offsetWidth + 16; // 16 is approximate width of scroll bar
				}
			}
		}
		else
		{
		    subMenu.style.height = (maxHeight + "px");
			subMenu.style.overflowY = "hidden";
		}
	}
}

function flyout_menu_onmouseover(el, menuID, parentId)
{
    var parent = document.getElementById(parentId);
	menu_onmouseover(el);

	var subMenu = document.getElementById(menuID);
	if (subMenu == null)
		return;

	submenu_adjustDimensions(subMenu);

	// See if we should cancel a previous attempt to hide this menu.
	if (subMenu == visibleSubMenu)
	{
		reenterMenuCount++;
	}
	else
	{
		// Position the submenu relative to its parent menu		
		subMenu.style.top = submenu_calcMenuTop(el, menuID, parent) - el.offsetHeight + "px";
		subMenu.style.left = (submenu_calcMenuLeft(el, parent) + el.offsetWidth - 3) + "px";
		subMenuToShow = subMenu;
		setTimeout("submenu_deferredDisplaySubMenu(\'" + menuID + "\')", 100);
	}
}

function flyout_submenu_onmouseover(el, menuID, parentId)
{
    var parent = document.getElementById(parentId);
	menu_onmouseover(el);

	var subMenu = document.getElementById(menuID);
	if (subMenu == null)
		return;

	submenu_adjustDimensions(subMenu);

	// See if we should cancel a previous attempt to hide this menu.
	if (subMenu == visibleSubMenu)
	{
		reenterMenuCount++;
	}
	else
	{
		// Position the submenu relative to its parent menu		
		subMenu.style.top = submenu_calcMenuTop(el, menuID, parent) - el.offsetHeight + "px";
		subMenu.style.left = (submenu_calcMenuLeft(el, parent) + el.offsetWidth - 3) + "px";
		subMenuToShow = subMenu;
		setTimeout("submenu_deferredDisplaySubMenu(\'" + menuID + "\')", 100);
	}
	
	
}

function submenu_onmouseover(el, menuID, parentId)
{
    var parent = document.getElementById(parentId);
	menu_onmouseover(el);
	var subMenu = document.getElementById(menuID);
	if (subMenu == null)
		return;

	submenu_adjustDimensions(subMenu);

	// See if we should cancel a previous attempt to hide this menu.
	if (subMenu == visibleSubMenu)
	{
		reenterMenuCount++;
	}
	else
	{
		// Position the submenu relative to its parent menu		
		subMenu.style.top = submenu_calcMenuTop(el, menuID, parent) + "px";
		subMenu.style.left = (submenu_calcMenuLeft(el, parent) + el.offsetWidth - subMenu.offsetWidth) + "px";
		subMenu.style.position= "relative";
		subMenu.style.zIndex="10";

		subMenuToShow = subMenu;
		setTimeout("submenu_deferredDisplaySubMenu(\'" + menuID + "\')", 0);
	}
	
	
}

function submenu_deferredDisplaySubMenu(menuID)
{
	var subMenu = document.getElementById(menuID);
	if (subMenu == null)
		return;
    DrawIframeBlocker(menuID);
	if (subMenu == subMenuToShow)
	{
		if (visibleSubMenu != subMenuToShow)
		{
			submenu_hide(menuID);
			visibleSubMenu = subMenu;
			subMenuToShow = null;
			subMenu.style.visibility = "visible";

			if (onWindowsIE)
			{
				// Look for the submenu container.
				var container = subMenu;
				while (container != null && container.className != "submenu_container")
					container = container.parentElement;
				if (container == null)
					return;
				
				container.style.zIndex = 5;
				submenu_makeDropShadow(container);
			}
			
		}
		
		
	}
	
}

function submenu_onmouseout(el, menuID)
{
	menu_onmouseout(el);

	var subMenu = document.getElementById(menuID);
	if (subMenu == null)
		return;

	if (subMenu == visibleSubMenu)
	{
		subMenuToHide = subMenu;
		
		// Schedule the submenu to go away if we don't re-enter the
		// submenu before the timer fires.
		setTimeout("submenu_deferredHideSubMenu(\'" + menuID + "\', " + reenterMenuCount + ")", 100);
	}
	else if (subMenu == subMenuToShow)
	{
		subMenuToShow = null;
	}
	
}

function flyout_menu_onmouseout(el, menuID)
{
    menu_onmouseout(el);
	var subMenu = document.getElementById(menuID);
	if (subMenu == null)
		return;

	if (subMenu == visibleSubMenu)
	{
		subMenuToHide = subMenu;
		
		// Schedule the submenu to go away if we don't re-enter the
		// submenu before the timer fires.
		setTimeout("submenu_deferredHideSubMenu(\'" + menuID + "\', " + reenterMenuCount + ")", 100);
	}
	else if (subMenu == subMenuToShow)
	{
		subMenuToShow = null;
	}
}


function submenu_deferredHideSubMenu(menuID, outCount)
{
	var subMenu = document.getElementById(menuID);
	if (subMenu == null)
		return;

	if (visibleSubMenu == subMenuToHide && 
		subMenu == subMenuToHide && 
		outCount == reenterMenuCount)
	{
        
		submenu_hide(menuID);
		
	}
}

function submenu_hide(menuID)
{
	if (visibleSubMenu != null)
	{
		if (onWindowsIE)
			submenu_destroyDropShadow();
        UnDrawIframeBlocker(menuID);
		visibleSubMenu.style.visibility = "hidden";
		visibleSubMenu = null;
		subMenuToHide = null;
	}
}

function submenu_makeDropShadow(subMenu)
{
	var rectIndex;
	
	for (rectIndex = 4; rectIndex > 0; rectIndex--)
	{
		var rect = document.createElement('div');
		var rectStyle = rect.style
		rectStyle.position = "absolute";
		rectStyle.left = (subMenu.style.posLeft + rectIndex) + 'px';
		rectStyle.top = (subMenu.style.posTop + rectIndex) + 'px';
		rectStyle.width = subMenu.offsetWidth + 'px';
		rectStyle.height = subMenu.offsetHeight + 'px';
		rectStyle.zIndex = subMenu.style.zIndex - rectIndex;
		rectStyle.backgroundColor = '#888888';
		var opacity = 1 - rectIndex / (rectIndex + 1);
		rectStyle.filter = "alpha(opacity = " + (100 * opacity) + ")";
		subMenu.insertAdjacentElement("afterEnd", rect);
		
		// Track the rects so we can destroy them later
		submenu_shadows[submenu_shadows.length] = rect;
	}
}

function submenu_destroyDropShadow()
{
	if (submenu_shadows != null)
	{
		var rectIndex;
		for (rectIndex = 0; rectIndex < submenu_shadows.length; rectIndex++)
			submenu_shadows[rectIndex].removeNode(true);
		submenu_shadows = new Array();
	}
}

function DrawIframeBlocker(elemID) {
    var DivRef=document.getElementById(elemID);
	var IfrRef = document.getElementById("PopUpDivShim");
    if(IfrRef!=null){
	
    // set IFrame shim
    DivRef.style.display = "block";
    IfrRef.style.width = DivRef.offsetWidth + "px";
    IfrRef.style.height = DivRef.offsetHeight + "px";
    IfrRef.style.top = DivRef.style.top;
    IfrRef.style.left = DivRef.style.left;
    IfrRef.style.zIndex = "0"; 
    IfrRef.style.display = "block";
    }
}

function UnDrawIframeBlocker(elemID) {
    var DivRef=document.getElementById(elemID);
	var IfrRef = document.getElementById("PopUpDivShim");
	if(IfrRef!=null){
        IfrRef.style.display = "none";
    }
}
