const form = document.querySelector(".filters");
const count = document.querySelector(".count");
const empty = document.querySelector(".empty");
const search = form.elements.namedItem("q");
const category = form.elements.namedItem("section");
const requirement = form.elements.namedItem("need");

function normalize(text) {
  return text.normalize("NFKC").toLowerCase();
}

const groups = Array.from(document.querySelectorAll(".group"), group => ({
  element: group,
  cards: Array.from(group.querySelectorAll(".card"), card => ({
    element: card,
    keywords: normalize(card.dataset.search),
  })),
}));

function filter() {
  const terms = normalize(search.value).trim().split(/\s+/);
  let total = 0;
  for (const {element: group, cards} of groups) {
    const inCategory = !category.value || group.dataset.section === category.value;
    let visible = 0;
    for (const {element: card, keywords} of cards) {
      const matches = inCategory
        && (!requirement.value || card.dataset.need === requirement.value)
        && terms.every(term => keywords.includes(term));
      card.hidden = !matches;
      visible += Number(matches);
    }
    group.hidden = visible === 0;
    total += visible;
  }
  count.textContent = `${total} 种画风`;
  empty.hidden = total > 0;
}

form.addEventListener("input", filter);
form.addEventListener("submit", event => event.preventDefault());
form.addEventListener("reset", () => requestAnimationFrame(filter));
window.addEventListener("pageshow", filter);
form.hidden = false;
filter();
