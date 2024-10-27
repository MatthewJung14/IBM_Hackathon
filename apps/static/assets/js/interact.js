interact('.draggable')
  .draggable({
    inertia: true,
    modifiers: [
      interact.modifiers.restrictRect({
        restriction: 'parent',
        endOnly: true
      })
    ],
    listeners: {
      move: dragMoveListener,
    }
  });

function dragMoveListener(event) {
  const target = event.target;
  // Keep the dragged position in the data-x/data-y attributes
  const x = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx;
  const y = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy;

  // Translate the element
  target.style.transform = `translate(${x}px, ${y}px)`;

  // Update the position attributes
  target.setAttribute('data-x', x);
  target.setAttribute('data-y', y);
}
