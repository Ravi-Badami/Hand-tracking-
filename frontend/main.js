const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.z = 3;

const renderer = new THREE.WebGLRenderer({ alpha: true });
document.body.appendChild(renderer.domElement);
renderer.setSize(window.innerWidth, window.innerHeight);

const connections = [
  [0,1],[1,2],[2,3],[3,4],
  [0,5],[5,6],[6,7],[7,8],
  [5,9],[9,10],[10,11],[11,12],
  [9,13],[13,14],[14,15],[15,16],
  [13,17],[17,18],[18,19],[19,20],
  [0,17]
];

const handObjects = [];

function createHand() {
  const points = [];
  for (let i = 0; i < 21; i++) {
    const sphere = new THREE.Mesh(
      new THREE.SphereGeometry(0.02),
      new THREE.MeshBasicMaterial({ color: 0x00ff00 })
    );
    scene.add(sphere);
    points.push(sphere);
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(new Array(connections.length * 6).fill(0), 3));
  const line = new THREE.LineSegments(
    geometry,
    new THREE.LineBasicMaterial({ color: 0xffff00 })
  );
  scene.add(line);

  const label = document.createElement("div");
  label.style.position = "absolute";
  label.style.color = "white";
  label.style.fontSize = "18px";
  label.style.fontWeight = "bold";
  label.style.backgroundColor = "rgba(0, 0, 0, 0.5)";
  label.style.padding = "4px 8px";
  label.style.borderRadius = "6px";
  label.innerText = "";
  document.body.appendChild(label);

  return { points, line, label };
}

function updateHand(hand, data) {
  for (let i = 0; i < 21; i++) {
    const [x, y, z] = data.landmarks[i];
    hand.points[i].position.set((x - 0.5) * 2, (-y + 0.5) * 2, z);
  }

  const positions = hand.line.geometry.attributes.position.array;
  connections.forEach((pair, i) => {
    const [a, b] = pair;
    const pa = hand.points[a].position;
    const pb = hand.points[b].position;
    positions.set([pa.x, pa.y, pa.z, pb.x, pb.y, pb.z], i * 6);
  });
  hand.line.geometry.attributes.position.needsUpdate = true;

  const pos = hand.points[0].position.clone();
  pos.project(camera);
  const screenX = (pos.x + 1) / 2 * window.innerWidth;
  const screenY = (-pos.y + 1) / 2 * window.innerHeight;

  hand.label.style.left = `${screenX}px`;
  hand.label.style.top = `${screenY}px`;
  hand.label.innerText = `${data.hand}
${data.gesture}
${data.pinch_status}`;
}

function fetchLandmarks() {
  fetch("http://localhost:5000/landmarks")
    .then(res => res.json())
    .then(data => {
      while (handObjects.length < data.length) {
        handObjects.push(createHand());
      }

      data.forEach((handData, i) => {
        updateHand(handObjects[i], handData);
      });

      for (let i = data.length; i < handObjects.length; i++) {
        handObjects[i].points.forEach(p => p.position.set(999, 999, 999));
        const posArr = handObjects[i].line.geometry.attributes.position.array;
        for (let j = 0; j < posArr.length; j++) posArr[j] = 999;
        handObjects[i].line.geometry.attributes.position.needsUpdate = true;
        handObjects[i].label.style.left = "-999px";
        handObjects[i].label.style.top = "-999px";
      }
    })
    .catch(err => console.error("API error:", err));
}

setInterval(fetchLandmarks, 66); // ~15 FPS

function animate() {
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}

animate();

const video = document.getElementById("video");
video.src = "http://localhost:5000/video";
