function triggerFileInput(categoryId) {
  const fileInput = document.getElementById(`${categoryId}-file`);
  if (fileInput) {
    fileInput.click();
  } else {
    console.error("File input not found for category", categoryId);
  }
}

function addCard(event) {
  const sourceElement = event.currentTarget;
  const categoryId = sourceElement.id.split("-")[0].match(/\d+/)[0];
  const titleInput = document.getElementById(`${categoryId}-new-card`);
  const fileInput = document.getElementById(`${categoryId}-file`);

  if (!titleInput) {
    alert("Title input not found!");
    return;
  }

  const formData = new FormData();
  formData.append("new_card_title", titleInput.value);
  formData.append("category_id", categoryId);

  if (fileInput && fileInput.files.length > 0) {
    formData.append("image", fileInput.files[0]);
  }

  fetch("/add-card/", {
    method: "POST",
    headers: {
      "X-CSRFToken": Cookies.get("csrftoken"),
    },
    body: formData,
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        const container = document.querySelector(
          `ul.category-inner-container[data-category-id="${data.category_id}"]`
        );
        const newCard = document.createElement("li");
        newCard.textContent = data.title;
        newCard.className = "card";
        newCard.dataset.cardId = data.card_id;
        container.appendChild(newCard);
        titleInput.value = "";
        if (fileInput) fileInput.value = "";
      } else {
        alert("Error: " + data.error);
      }
    });
}
