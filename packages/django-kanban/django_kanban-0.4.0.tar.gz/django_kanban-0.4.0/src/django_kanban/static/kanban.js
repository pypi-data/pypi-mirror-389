function openColorModal(button) {
  const colorContainer = button.parentElement.querySelector(".color-container");

  if (colorContainer.style.display === "flex") {
    colorContainer.style.display = "none";
  } else {
    colorContainer.style.display = "flex";
  }
}

function openBoardModal() {
  const boardModal = document.getElementById("board-modal");

  if (boardModal.style.display === "flex") {
    boardModal.style.display = "none";
  } else {
    boardModal.style.display = "flex";
  }
}

const EDGE_MARGIN = 150;
const MAX_SPEED = 40;
let scrollSpeed = 0;
let rafId = null;

const scrollContainer = document.getElementById("board");
const board = document.getElementById("board");

function smoothScroll() {
  scrollContainer.scrollLeft += scrollSpeed;
  rafId = scrollSpeed !== 0 ? requestAnimationFrame(smoothScroll) : null;
}

function calculateScrollSpeed(clientX) {
  if (clientX < EDGE_MARGIN) {
    return -Math.min(
      MAX_SPEED,
      ((EDGE_MARGIN - clientX) / EDGE_MARGIN) * MAX_SPEED
    );
  }
  if (clientX > window.innerWidth - EDGE_MARGIN) {
    return Math.min(
      MAX_SPEED,
      ((clientX - (window.innerWidth - EDGE_MARGIN)) / EDGE_MARGIN) * MAX_SPEED
    );
  }
  return 0;
}

function onDragOver(e) {
  const newSpeed = calculateScrollSpeed(e.clientX);
  if (newSpeed !== scrollSpeed) {
    scrollSpeed = newSpeed;
    if (scrollSpeed !== 0 && rafId === null) {
      rafId = requestAnimationFrame(smoothScroll);
    } else if (scrollSpeed === 0 && rafId !== null) {
      cancelAnimationFrame(rafId);
      rafId = null;
    }
  }
}

function stopScrolling() {
  scrollSpeed = 0;
  if (rafId !== null) {
    cancelAnimationFrame(rafId);
    rafId = null;
  }
}

function onDragStart() {}

board.addEventListener("dragover", onDragOver);
board.addEventListener("dragenter", (e) => e.preventDefault());
board.addEventListener("dragstart", onDragStart, true);
board.addEventListener("dragend", stopScrolling, true);
board.addEventListener("drop", stopScrolling, true);
