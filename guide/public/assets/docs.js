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
    if (!element) {
        return false;
    }
    let nextElementSibling = element.nextElementSibling;
    let menuList = null;
    while (!menuList && nextElementSibling) {
        if (nextElementSibling.classList.contains("menu-list")) {
            menuList = nextElementSibling;
        } else {
            nextElementSibling = nextElementSibling.nextElementSibling;
        }
    }
    if (menuList) {
        const siblinkLinks = [...menuList.querySelectorAll("a")];
        return siblinkLinks.some((el) => el.classList.contains("is-active"));
    }
    return false;
}
function initBurger() {
    if (!burger || !menu) {
        return;
    }
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
function initDetails() {
    const detailsElements = document.querySelectorAll(".details");
    detailsElements.forEach((element) => {
        element.addEventListener("click", function () {
            this.classList.toggle("is-active");
        });
    });
}
function initTabs() {
    const tabsElements = document.querySelectorAll(".tabs");

    tabsElements.forEach((element) => {
        const tabTriggers = element.querySelectorAll("li>a");
        const tabs = element.querySelectorAll("li");
        tabTriggers.forEach((trigger) => {
            trigger.addEventListener("click", function () {
                tabs.forEach((tab) => {
                    tab.classList.remove("is-active");
                });
                const content = this.nextElementSibling;
                // this.parentElement.querySelector(".tab-content");
                this.parentElement.classList.add("is-active");
                const tabDisplay =
                    this.parentElement.parentElement.parentElement
                        .nextElementSibling;
                tabDisplay.innerHTML = content.innerHTML;
            });
        });
        const firstTabTrigger = tabTriggers[0];
        firstTabTrigger.click();
    });
}
function initSearch() {
    const searchInput = document.querySelector("#search");
    searchInput.addEventListener("keyup", () => {
        const value = searchInput.value;
        searchInput.setAttribute(
            "hx-vals",
            `{"q": "${encodeURIComponent(value)}"}`
        );
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
function copyCode(button) {
    const codeBlock = button.parentElement;
    const code = codeBlock.querySelector("code").innerText;
    const textarea = document.createElement("textarea");
    textarea.value = code;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    document.body.removeChild(textarea);

    button.classList.add("clicked"); // Add class for animation

    setTimeout(() => {
        button.classList.remove("clicked"); // Remove class to revert to original state
    }, 1500);
}
function init() {
    refreshBurger();
    refreshMenu();
    refreshMenuLinks();
    refreshMenuGroups();
    initBurger();
    initMenuGroups();
    initDetails();
    initTabs();
    initSearch();
}

function afterSwap(e) {
    setMenuLinkActive(e.detail.pathInfo.requestPath);
    window.scrollTo(0, 0);
}
document.addEventListener("DOMContentLoaded", init);
document.body.addEventListener("htmx:afterSwap", afterSwap);
