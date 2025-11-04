function addCategory() {
  const newCategoryName = document.getElementById("new-category").value;
  fetch("/add-category/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": Cookies.get("csrftoken"),
    },
    body: JSON.stringify({
      board_id: 1,
      new_category_name: newCategoryName,
    }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        const container = document.getElementById("board");

        const newCategoryContainer = document.createElement("div");
        newCategoryContainer.className = "category-container";
        newCategoryContainer.setAttribute("data-category-id", data.category_id);
        newCategoryContainer.style.backgroundColor = data.color;

        newCategoryContainer.innerHTML = `
            <h2>${data.name} ${data.position}</h2>
            <button onclick="openColorModal(this)" class="color-button">&#8943;</button>
            <form method="post" id="${data.category_id}-color-form" class="color-container">
                <input type="hidden" name="csrfmiddlewaretoken" value="${data.csrf_token}">
                <label for="color">Pick a color:</label>
                <input type="color" id="color" name="color" value="${data.color}">
                <input type="hidden" id="category_id" name="category_id" value="${data.category_id}">
                <button type="submit">Submit</button>
            </form>
            <ul class="category-inner-container" data-category-id="${data.category_id}">
                <!-- Cards will be added here -->
            </ul>
            <div class="add-card-container">
                <input type="text" style="background-color: ${data.color}" id="${data.category_id}-new-card" placeholder="Add New Card">
                <button id="${data.category_id}-button" style="background-color: ${data.color}" onclick="addCard(event)">+</button>
            </div>
        `;

        container.appendChild(newCategoryContainer);
        document.getElementById("new-category").value = "";
      } else {
        alert("Error: " + data.error);
      }
    });
}
