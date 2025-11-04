document.addEventListener("DOMContentLoaded", () => {
  const categories = document.querySelectorAll(".category-inner-container");

  categories.forEach((category) => {
    new Sortable(category, {
      group: "shared",
      animation: 150,
      onEnd: function (evt) {
        const cardId = evt.item.dataset.cardId;
        console.log("Dragged card ID:", cardId);

        const newCategoryId = evt.to.dataset.categoryId;
        console.log("New category ID (column dropped into):", newCategoryId);

        const newPosition = evt.newIndex;
        console.log("New position (index in list):", newPosition);

        fetch("/update-card-position/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": Cookies.get("csrftoken"),
          },
          body: JSON.stringify({
            card_id: cardId,
            new_category_id: newCategoryId,
            new_position: newPosition,
          }),
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.success) {
              console.log("Card position updated successfully!");
            } else {
              console.error("Error updating card position");
            }
          })
          .catch((error) => {
            console.error("Error:", error);
          });
      },
    });
  });

  const board = document.getElementById("board");
  new Sortable(board, {
    animation: 150,
    draggable: ".category-container",
    onEnd: function (evt) {
      const categoryId = evt.item.dataset.categoryId;
      console.log("Dragged category ID:", categoryId);

      const newPosition = evt.newIndex;
      console.log("New category position:", newPosition);

      fetch("/update-category-position/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": Cookies.get("csrftoken"),
        },
        body: JSON.stringify({
          category_id: categoryId,
          new_position: newPosition,
        }),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            console.log("Category position updated successfully!");
          } else {
            console.error("Error updating category position");
          }
        })
        .catch((error) => {
          console.error("Error:", error);
        });
    },
  });
});
