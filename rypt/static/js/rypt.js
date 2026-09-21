(function () {
    var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var preloader = document.querySelector(".preloader");
    var themeBtn = document.querySelector(".theme");
    var root = document.documentElement;
    var deck = document.querySelector(".deck");
    var railGlass = document.querySelector(".rail-glass");
    var railBar = document.querySelector(".rail-bar");

    function setTheme(name) {
        root.setAttribute("data-theme", name);
        try { localStorage.setItem("rypt-theme", name); } catch (e) {}
    }

    function endRadius(x, y) {
        return Math.hypot(
            Math.max(x, window.innerWidth - x),
            Math.max(y, window.innerHeight - y)
        );
    }

    function toggleTheme(event) {
        var next = root.getAttribute("data-theme") === "light" ? "dark" : "light";
        if (reduce) {
            setTheme(next);
            return;
        }
        var x = event.clientX;
        var y = event.clientY;
        var radius = endRadius(x, y);
        if (document.startViewTransition) {
            var transition = document.startViewTransition(function () {
                setTheme(next);
            });
            transition.ready.then(function () {
                root.animate(
                    {
                        clipPath: [
                            "circle(0px at " + x + "px " + y + "px)",
                            "circle(" + radius + "px at " + x + "px " + y + "px)"
                        ]
                    },
                    {
                        duration: 720,
                        easing: "cubic-bezier(0.76, 0, 0.24, 1)",
                        pseudoElement: "::view-transition-new(root)"
                    }
                );
            });
            return;
        }
        var overlay = document.createElement("div");
        overlay.className = "theme-wipe";
        overlay.style.background = next === "light" ? "#e8e8e8" : "#222222";
        overlay.style.clipPath = "circle(0px at " + x + "px " + y + "px)";
        document.body.appendChild(overlay);
        requestAnimationFrame(function () {
            overlay.style.clipPath = "circle(" + radius + "px at " + x + "px " + y + "px)";
        });
        overlay.addEventListener("transitionend", function () {
            setTheme(next);
            overlay.remove();
        }, { once: true });
    }

    if (themeBtn) themeBtn.addEventListener("click", toggleTheme);

    if (railGlass && !reduce) {
        railGlass.addEventListener("pointermove", function (event) {
            var box = railGlass.getBoundingClientRect();
            railGlass.style.setProperty("--gx", (event.clientX - box.left) + "px");
            railGlass.style.setProperty("--gy", (event.clientY - box.top) + "px");
        });
    }

    function hidePreloader() {
        if (!preloader) return;
        preloader.classList.add("is-gone");
        preloader.style.display = "none";
    }

    function startDeck() {
        if (!deck) return;
        var originals = Array.prototype.slice.call(deck.querySelectorAll(".slide"));
        var n = originals.length;
        if (!n) return;
        var start = parseInt(deck.getAttribute("data-index") || "0", 10);
        if (isNaN(start) || start < 0 || start >= n) start = 0;

        var firstClone = originals[0].cloneNode(true);
        var lastClone = originals[n - 1].cloneNode(true);
        firstClone.setAttribute("aria-hidden", "true");
        lastClone.setAttribute("aria-hidden", "true");
        deck.appendChild(firstClone);
        deck.insertBefore(lastClone, originals[0]);

        var pos = start + 1;
        var moving = false;

        function apply(animate) {
            if (animate && !reduce) deck.classList.add("is-moving");
            else deck.classList.remove("is-moving");
            deck.style.transform = "translate3d(" + (-pos * 100) + "vw,0,0)";
        }

        function realIndex() {
            if (pos === 0) return n - 1;
            if (pos === n + 1) return 0;
            return pos - 1;
        }

        function syncChrome() {
            var i = realIndex();
            var slide = originals[i];
            if (slide && slide.dataset.title) document.title = slide.dataset.title;
            if (railBar) {
                Array.prototype.forEach.call(railBar.querySelectorAll("a[data-slide]"), function (a) {
                    a.classList.toggle("is-now", a.getAttribute("data-slide") === String(i));
                });
            }
        }

        function go(nextPos, animate) {
            if (moving && animate) return;
            pos = nextPos;
            var canAnimate = animate && !reduce;
            if (canAnimate) moving = true;
            apply(canAnimate);
            if (!canAnimate) {
                if (pos === 0) pos = n;
                else if (pos === n + 1) pos = 1;
                apply(false);
            }
            syncChrome();
            var i = realIndex();
            var slide = originals[i];
            if (slide && slide.dataset.url) {
                var nextUrl = slide.dataset.url;
                if (window.location.pathname !== nextUrl) {
                    history.pushState({ pos: pos }, "", nextUrl);
                }
            }
        }

        deck.addEventListener("transitionend", function (event) {
            if (event.target !== deck || event.propertyName !== "transform") return;
            moving = false;
            if (pos === 0) {
                pos = n;
                apply(false);
            } else if (pos === n + 1) {
                pos = 1;
                apply(false);
            }
        });

        apply(false);
        syncChrome();

        document.querySelectorAll(".flip-prev").forEach(function (btn) {
            btn.addEventListener("click", function () { go(pos - 1, true); });
        });
        document.querySelectorAll(".flip-next").forEach(function (btn) {
            btn.addEventListener("click", function () { go(pos + 1, true); });
        });

        if (railBar) {
            railBar.addEventListener("click", function (event) {
                var a = event.target.closest("a[data-slide]");
                if (!a) return;
                event.preventDefault();
                var i = parseInt(a.getAttribute("data-slide"), 10);
                if (isNaN(i)) return;
                go(i + 1, true);
            });
        }

        var brand = document.querySelector(".chrome .brand");
        if (brand) {
            brand.addEventListener("click", function (event) {
                event.preventDefault();
                go(1, true);
            });
        }

        document.addEventListener("keydown", function (event) {
            if (event.target && /input|textarea|select/i.test(event.target.tagName)) return;
            if (event.key === "ArrowLeft") {
                event.preventDefault();
                go(pos - 1, true);
            }
            if (event.key === "ArrowRight") {
                event.preventDefault();
                go(pos + 1, true);
            }
        });

        var startX = 0;
        var startY = 0;
        var tracking = false;
        deck.addEventListener("pointerdown", function (event) {
            if (event.pointerType === "mouse") return;
            tracking = true;
            startX = event.clientX;
            startY = event.clientY;
        });
        window.addEventListener("pointerup", function (event) {
            if (!tracking) return;
            tracking = false;
            var dx = event.clientX - startX;
            var dy = event.clientY - startY;
            if (Math.abs(dx) < 70 || Math.abs(dx) < Math.abs(dy) * 1.6) return;
            if (dx < 0) go(pos + 1, true);
            else go(pos - 1, true);
        });

        window.addEventListener("popstate", function () {
            var path = window.location.pathname;
            var i = originals.findIndex(function (slide) {
                return slide.dataset.url === path || (path === "/" && slide.dataset.url === "/");
            });
            if (i < 0) return;
            pos = i + 1;
            apply(false);
            syncChrome();
        });
    }

    function startSeasonTabs() {
        var root = document.querySelector("[data-season-tabs]");
        if (!root) return;
        var tabs = Array.prototype.slice.call(root.querySelectorAll("[role=tab]"));
        var panels = Array.prototype.slice.call(root.querySelectorAll("[role=tabpanel]"));
        if (!tabs.length) return;

        function show(name, updateHash) {
            var found = false;
            tabs.forEach(function (tab) {
                var on = tab.getAttribute("data-tab") === name;
                tab.setAttribute("aria-selected", on ? "true" : "false");
                tab.tabIndex = on ? 0 : -1;
                if (on) found = true;
            });
            if (!found) {
                name = tabs[0].getAttribute("data-tab");
                tabs[0].setAttribute("aria-selected", "true");
                tabs[0].tabIndex = 0;
            }
            panels.forEach(function (panel) {
                var on = panel.id === "panel-" + name;
                if (on) panel.removeAttribute("hidden");
                else panel.setAttribute("hidden", "");
            });
            if (updateHash) {
                var next = "#" + name;
                if (window.location.hash !== next) {
                    history.replaceState(null, "", next);
                }
            }
        }

        var initial = (window.location.hash || "").replace("#", "");
        show(initial || tabs[0].getAttribute("data-tab"), false);

        root.addEventListener("click", function (event) {
            var tab = event.target.closest("[role=tab]");
            if (!tab || !root.contains(tab)) return;
            show(tab.getAttribute("data-tab"), true);
        });

        root.addEventListener("keydown", function (event) {
            var tab = event.target.closest("[role=tab]");
            if (!tab || !root.contains(tab)) return;
            var i = tabs.indexOf(tab);
            if (i < 0) return;
            var next = i;
            if (event.key === "ArrowRight" || event.key === "ArrowDown") next = (i + 1) % tabs.length;
            else if (event.key === "ArrowLeft" || event.key === "ArrowUp") next = (i - 1 + tabs.length) % tabs.length;
            else if (event.key === "Home") next = 0;
            else if (event.key === "End") next = tabs.length - 1;
            else return;
            event.preventDefault();
            tabs[next].focus();
            show(tabs[next].getAttribute("data-tab"), true);
        });

        window.addEventListener("hashchange", function () {
            show((window.location.hash || "").replace("#", ""), false);
        });
    }

    function startPhotoStudio() {
        var root = document.querySelector("[data-photo-studio]");
        if (!root) return;

        var switches = Array.prototype.slice.call(root.querySelectorAll("[data-album-view]"));
        var panes = Array.prototype.slice.call(root.querySelectorAll("[data-album-pane]"));
        function showAlbum(name) {
            switches.forEach(function (btn) {
                var on = btn.getAttribute("data-album-view") === name;
                btn.classList.toggle("is-on", on);
                btn.setAttribute("aria-selected", on ? "true" : "false");
            });
            panes.forEach(function (pane) {
                var on = pane.getAttribute("data-album-pane") === name;
                if (on) pane.removeAttribute("hidden");
                else pane.setAttribute("hidden", "");
            });
        }
        switches.forEach(function (btn) {
            btn.addEventListener("click", function () {
                showAlbum(btn.getAttribute("data-album-view"));
            });
        });

        var thumbs = Array.prototype.slice.call(root.querySelectorAll(".photo-thumb"));
        var frame = root.querySelector(".photo-frame img");
        var caption = root.querySelector(".photo-frame figcaption");
        var count = root.querySelector("[data-photo-count]");
        var original = root.querySelector("[data-photo-original]");
        var prev = root.querySelector(".photo-prev");
        var next = root.querySelector(".photo-next");
        if (!thumbs.length || !frame) return;
        var index = 0;

        function show(i) {
            if (!thumbs.length) return;
            index = (i + thumbs.length) % thumbs.length;
            var thumb = thumbs[index];
            frame.src = thumb.getAttribute("data-src") || "";
            frame.alt = thumb.getAttribute("aria-label") || "";
            frame.referrerPolicy = "no-referrer";
            if (caption) caption.textContent = thumb.getAttribute("data-caption") || "";
            if (count) count.textContent = (index + 1) + " / " + thumbs.length;
            if (original) {
                var href = thumb.getAttribute("data-original") || "";
                original.href = href;
                original.hidden = !href;
            }
            thumbs.forEach(function (el, n) {
                el.classList.toggle("is-on", n === index);
            });
        }

        thumbs.forEach(function (thumb, i) {
            thumb.addEventListener("click", function () {
                show(i);
                showAlbum("carousel");
            });
        });
        if (prev) prev.addEventListener("click", function () { show(index - 1); });
        if (next) next.addEventListener("click", function () { show(index + 1); });
        show(0);
    }

    startDeck();
    startSeasonTabs();
    startPhotoStudio();

    if (!preloader || reduce || typeof anime === "undefined") {
        hidePreloader();
        return;
    }

    var orb = preloader.querySelector(".preloader-orb");
    anime.timeline({ easing: "easeInOutCubic" })
        .add({
            targets: orb,
            scale: [0.15, 1.2, 1],
            duration: 680
        })
        .add({
            targets: preloader,
            clipPath: ["circle(150% at 50% 50%)", "circle(0% at 50% 50%)"],
            duration: 780,
            complete: hidePreloader
        });
})();
