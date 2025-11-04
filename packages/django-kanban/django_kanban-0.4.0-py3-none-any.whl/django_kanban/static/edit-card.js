function editCard(event) {
  const card = event.parentElement;
  const cardTitle = card.querySelector("p, a");
  const isEditable = cardTitle.getAttribute("contenteditable") === "true";
  cardTitle.setAttribute("contenteditable", !isEditable);
  cardTitle.focus();

  if (!isEditable) {
    cardTitle.style.border = "1px dashed #999";
  } else {
    cardTitle.style.border = "";
    const newCardTitle = cardTitle.textContent;
    const cardId = card.dataset.cardId;

    fetch("/edit-card/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": Cookies.get("csrftoken"),
      },
      body: JSON.stringify({
        'new_card_title': newCardTitle,
        'card_id': cardId,
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          console.log("Card successfully updated")
        } else {
          alert("Error: " + data.error);
        }
      });
  }
}
