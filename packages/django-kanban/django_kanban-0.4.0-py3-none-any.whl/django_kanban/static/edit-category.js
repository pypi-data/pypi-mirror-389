const categoryName = document.getElementsByClassName("category-name");

Array.from(categoryName).forEach(function(categoryName) {
  categoryName.addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
      event.preventDefault();

      const newCategoryName = categoryName.textContent
      const parentContainer = categoryName.parentElement
      const categoryId = parentContainer ? parentContainer.getAttribute("data-category-id") : null;

      console.log("User entered:", newCategoryName);
      console.log("Parent container data-id:", categoryId);

      fetch("/edit-category/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": Cookies.get("csrftoken"),
        },
        body: JSON.stringify({
          'new_category_title': newCategoryName,
          'category_id': categoryId,
        }),
      })    
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          console.log("Category successfully updated")
        } else {
          alert("Error: " + data.error);
        }
      });

    }
  });
});

  