const source = new EventSource(
  "/api/v1/live/class-board"
);

source.addEventListener(
  "class-board",
  (event) => {
    const board = JSON.parse(event.data);

    console.log(board);
  }
);