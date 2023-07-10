let burger;
let menu;
let menuLinks;
let menuGroups;
function trigger(el, eventType) {
    if (typeof eventType === "string" && typeof el[eventType] === "function") {
        el[eventType]();
    } else {
        const event =
            typeof eventType === "string"
                ? new Event(eventType, { bubbles: true })
                : eventType;
        el.dispatchEvent(event);
    }
}
function refreshBurger() {
    burger = document.querySelector(".burger");
}
function refreshMenu() {
    menu = document.querySelector(".menu");
}
function refreshMenuLinks() {
    menuLinks = document.querySelectorAll(".menu a[hx-get]");
}
function refreshMenuGroups() {
    menuGroups = document.querySelectorAll(".menu li.is-group a:not([href])");
}
function hasActiveLink(element) {
    const menuList = element.nextElementSibling;
    if (menuList) {
        const siblinkLinks = [...menuList.querySelectorAll("a")];
        return siblinkLinks.some((el) => el.classList.contains("is-active"));
    }
    return false;
}
function initBurger() {
    burger.addEventListener("click", (e) => {
        e.preventDefault();
        burger.classList.toggle("is-active");
        menu.classList.toggle("is-active");
    });
}
function initMenuGroups() {
    menuGroups.forEach((el) => {
        el.addEventListener("click", (e) => {
            e.preventDefault();
            menuGroups.forEach((g) => {
                if (g === el) {
                    g.classList.toggle("is-open");
                } else {
                    g.classList.remove("is-open");
                }
            });
        });
    });
}
function setMenuLinkActive(href) {
    burger.classList.remove("is-active");
    menu.classList.remove("is-active");
    menuLinks.forEach((element) => {
        if (element.attributes.href.value === href) {
            element.classList.add("is-active");
        } else {
            element.classList.remove("is-active");
        }
    });
    menuGroups.forEach((g) => {
        if (hasActiveLink(g)) {
            g.classList.add("is-open");
        } else {
            g.classList.remove("is-open");
        }
    });
}
function init() {
    refreshBurger();
    refreshMenu();
    refreshMenuLinks();
    refreshMenuGroups();
    initBurger();
    initMenuGroups();
}
function afterSwap(e) {
    setMenuLinkActive(e.detail.pathInfo.requestPath);
    window.scrollTo(0, 0);
}
document.addEventListener("DOMContentLoaded", init);
document.body.addEventListener("htmx:afterSwap", afterSwap);
