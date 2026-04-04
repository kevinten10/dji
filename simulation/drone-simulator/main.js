// DJI 3D无人机模拟器
// 使用Three.js构建的3D无人机飞行模拟器

let scene, camera, renderer, controls;
let drone, droneGroup;
let propellers = [];
let ground, gridHelper;

// 无人机状态
const droneState = {
    position: new THREE.Vector3(0, 5, 0),
    rotation: new THREE.Euler(0, 0, 0),
    velocity: new THREE.Vector3(0, 0, 0),
    speed: 0.15,
    rotationSpeed: 0.03,
    maxTilt: Math.PI / 6
};

// 按键状态
const keys = {
    w: false, s: false, a: false, d: false,
    ArrowUp: false, ArrowDown: false, ArrowLeft: false, ArrowRight: false
};

// 初始化场景
function init() {
    // 创建场景
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1a2e);
    scene.fog = new THREE.Fog(0x1a1a2e, 50, 200);

    // 创建相机
    camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.set(15, 15, 15);

    // 创建渲染器
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    document.getElementById('container').appendChild(renderer.domElement);

    // 创建控制器
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxDistance = 100;
    controls.minDistance = 5;

    // 添加光源
    setupLights();

    // 创建地面
    createGround();

    // 创建无人机
    createDrone();

    // 创建环境物体
    createEnvironment();

    // 添加事件监听
    setupEventListeners();

    // 开始动画循环
    animate();
}

function setupLights() {
    // 环境光
    const ambientLight = new THREE.AmbientLight(0x404060, 0.5);
    scene.add(ambientLight);

    // 主光源
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(50, 100, 50);
    directionalLight.castShadow = true;
    directionalLight.shadow.mapSize.width = 2048;
    directionalLight.shadow.mapSize.height = 2048;
    directionalLight.shadow.camera.near = 0.5;
    directionalLight.shadow.camera.far = 500;
    directionalLight.shadow.camera.left = -100;
    directionalLight.shadow.camera.right = 100;
    directionalLight.shadow.camera.top = 100;
    directionalLight.shadow.camera.bottom = -100;
    scene.add(directionalLight);

    // 补充光
    const fillLight = new THREE.DirectionalLight(0x00d4ff, 0.3);
    fillLight.position.set(-50, 50, -50);
    scene.add(fillLight);
}

function createGround() {
    // 主地面
    const groundGeometry = new THREE.PlaneGeometry(200, 200);
    const groundMaterial = new THREE.MeshStandardMaterial({ 
        color: 0x2a2a4a,
        roughness: 0.8,
        metalness: 0.2
    });
    ground = new THREE.Mesh(groundGeometry, groundMaterial);
    ground.rotation.x = -Math.PI / 2;
    ground.receiveShadow = true;
    scene.add(ground);

    // 网格辅助线
    gridHelper = new THREE.GridHelper(200, 50, 0x00d4ff, 0x333366);
    gridHelper.position.y = 0.01;
    scene.add(gridHelper);
}

function createDrone() {
    droneGroup = new THREE.Group();

    // 机身
    const bodyGeometry = new THREE.BoxGeometry(1.5, 0.4, 1.5);
    const bodyMaterial = new THREE.MeshStandardMaterial({ 
        color: 0x333344,
        metalness: 0.8,
        roughness: 0.3
    });
    const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
    body.castShadow = true;
    droneGroup.add(body);

    // 机臂
    const armGeometry = new THREE.CylinderGeometry(0.08, 0.08, 1.2);
    const armMaterial = new THREE.MeshStandardMaterial({ color: 0x222233 });
    
    const armPositions = [
        { x: 0.8, z: 0.8, rotZ: Math.PI / 4 },
        { x: -0.8, z: 0.8, rotZ: -Math.PI / 4 },
        { x: 0.8, z: -0.8, rotZ: -Math.PI / 4 },
        { x: -0.8, z: -0.8, rotZ: Math.PI / 4 }
    ];

    armPositions.forEach(pos => {
        const arm = new THREE.Mesh(armGeometry, armMaterial);
        arm.position.set(pos.x, 0, pos.z);
        arm.rotation.z = pos.rotZ;
        arm.castShadow = true;
        droneGroup.add(arm);
    });

    // 螺旋桨
    const propellerGeometry = new THREE.BoxGeometry(0.8, 0.02, 0.1);
    const propellerMaterial = new THREE.MeshStandardMaterial({ 
        color: 0x00d4ff,
        transparent: true,
        opacity: 0.7
    });

    const propellerPositions = [
        { x: 1.2, z: 1.2, dir: 1 },
        { x: -1.2, z: 1.2, dir: -1 },
        { x: 1.2, z: -1.2, dir: -1 },
        { x: -1.2, z: -1.2, dir: 1 }
    ];

    propellerPositions.forEach((pos, i) => {
        const propeller = new THREE.Group();
        propeller.position.set(pos.x, 0.2, pos.z);
        
        // 左右两个桨叶
        const blade1 = new THREE.Mesh(propellerGeometry, propellerMaterial);
        const blade2 = new THREE.Mesh(propellerGeometry, propellerMaterial);
        blade2.rotation.y = Math.PI / 2;
        
        propeller.add(blade1);
        propeller.add(blade2);
        propeller.userData.speed = pos.dir * 0.3;
        droneGroup.add(propeller);
        propellers.push(propeller);
    });

    // 云台相机
    const gimbalGeometry = new THREE.SphereGeometry(0.25);
    const gimbalMaterial = new THREE.MeshStandardMaterial({ color: 0x111122 });
    const gimbal = new THREE.Mesh(gimbalGeometry, gimbalMaterial);
    gimbal.position.set(0, -0.3, 0.3);
    droneGroup.add(gimbal);

    // 相机镜头
    const lensGeometry = new THREE.CylinderGeometry(0.08, 0.1, 0.1);
    const lensMaterial = new THREE.MeshStandardMaterial({ color: 0x00ff88, emissive: 0x003322 });
    const lens = new THREE.Mesh(lensGeometry, lensMaterial);
    lens.rotation.x = Math.PI / 2;
    lens.position.set(0, -0.3, 0.4);
    droneGroup.add(lens);

    // LED灯
    const ledGeometry = new THREE.SphereGeometry(0.05);
    const ledMaterial = new THREE.MeshBasicMaterial({ color: 0xff0000 });
    const led1 = new THREE.Mesh(ledGeometry, ledMaterial);
    led1.position.set(-0.6, 0, -0.6);
    droneGroup.add(led1);

    const ledMaterial2 = new THREE.MeshBasicMaterial({ color: 0x00ff00 });
    const led2 = new THREE.Mesh(ledGeometry, ledMaterial2);
    led2.position.set(0.6, 0, -0.6);
    droneGroup.add(led2);

    droneGroup.position.copy(droneState.position);
    scene.add(droneGroup);
}

function createEnvironment() {
    // 创建一些随机的建筑物/障碍物
    const buildingGeometry = new THREE.BoxGeometry(1, 1, 1);
    const buildingMaterial = new THREE.MeshStandardMaterial({ 
        color: 0x4444aa,
        transparent: true,
        opacity: 0.8
    });

    for (let i = 0; i < 30; i++) {
        const height = Math.random() * 8 + 2;
        const building = new THREE.Mesh(buildingGeometry, buildingMaterial);
        building.position.set(
            (Math.random() - 0.5) * 80,
            height / 2,
            (Math.random() - 0.5) * 80
        );
        building.scale.y = height;
        building.castShadow = true;
        building.receiveShadow = true;
        scene.add(building);
    }

    // 添加一些树
    const treeGeometry = new THREE.ConeGeometry(1, 3);
    const treeMaterial = new THREE.MeshStandardMaterial({ color: 0x226622 });

    for (let i = 0; i < 20; i++) {
        const tree = new THREE.Mesh(treeGeometry, treeMaterial);
        tree.position.set(
            (Math.random() - 0.5) * 100,
            1.5,
            (Math.random() - 0.5) * 100
        );
        tree.castShadow = true;
        scene.add(tree);
    }

    // 添加灯光标记
    const lightPoleGeometry = new THREE.CylinderGeometry(0.1, 0.1, 5);
    const lightPoleMaterial = new THREE.MeshStandardMaterial({ color: 0x666666 });

    for (let i = 0; i < 8; i++) {
        const angle = (i / 8) * Math.PI * 2;
        const radius = 40;
        const pole = new THREE.Mesh(lightPoleGeometry, lightPoleMaterial);
        pole.position.set(Math.cos(angle) * radius, 2.5, Math.sin(angle) * radius);
        scene.add(pole);

        const lightGeometry = new THREE.SphereGeometry(0.3);
        const lightMaterial = new THREE.MeshBasicMaterial({ color: 0xffff00 });
        const light = new THREE.Mesh(lightGeometry, lightMaterial);
        light.position.set(Math.cos(angle) * radius, 5, Math.sin(angle) * radius);
        scene.add(light);
    }
}

function setupEventListeners() {
    // 键盘事件
    window.addEventListener('keydown', (e) => {
        const key = e.key.toLowerCase();
        if (key in keys) keys[key] = true;
        if (e.key in keys) keys[e.key] = true;
        if (key === 'r') resetDrone();
    });

    window.addEventListener('keyup', (e) => {
        const key = e.key.toLowerCase();
        if (key in keys) keys[key] = false;
        if (e.key in keys) keys[e.key] = false;
    });

    // 窗口大小调整
    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
}

function resetDrone() {
    droneState.position.set(0, 5, 0);
    droneState.rotation.set(0, 0, 0);
    droneState.velocity.set(0, 0, 0);
}

function updateDrone() {
    // 旋转（偏航）
    if (keys.a) droneState.rotation.y += droneState.rotationSpeed;
    if (keys.d) droneState.rotation.y -= droneState.rotationSpeed;

    // 计算朝向
    const direction = new THREE.Vector3(0, 0, -1);
    direction.applyEuler(droneState.rotation);

    // 前后移动
    if (keys.ArrowUp) {
        droneState.position.add(direction.clone().multiplyScalar(droneState.speed));
    }
    if (keys.ArrowDown) {
        droneState.position.add(direction.clone().multiplyScalar(-droneState.speed));
    }

    // 左右平移
    const right = new THREE.Vector3(1, 0, 0);
    right.applyEuler(droneState.rotation);
    if (keys.ArrowLeft) {
        droneState.position.add(right.clone().multiplyScalar(-droneState.speed));
    }
    if (keys.ArrowRight) {
        droneState.position.add(right.clone().multiplyScalar(droneState.speed));
    }

    // 上升下降
    if (keys.w) droneState.position.y += droneState.speed;
    if (keys.s) droneState.position.y -= droneState.speed;

    // 边界限制
    droneState.position.y = Math.max(0.5, Math.min(50, droneState.position.y));
    droneState.position.x = Math.max(-80, Math.min(80, droneState.position.x));
    droneState.position.z = Math.max(-80, Math.min(80, droneState.position.z));

    // 计算速度
    droneState.velocity.copy(droneState.position).sub(droneGroup.position);

    // 更新无人机位置和旋转
    droneGroup.position.copy(droneState.position);
    droneGroup.rotation.y = droneState.rotation.y;

    // 倾斜效果
    let tiltX = 0, tiltZ = 0;
    if (keys.ArrowUp) tiltX = -0.2;
    if (keys.ArrowDown) tiltX = 0.2;
    if (keys.ArrowLeft) tiltZ = 0.2;
    if (keys.ArrowRight) tiltZ = -0.2;

    droneGroup.children[0].rotation.x = THREE.MathUtils.lerp(droneGroup.children[0].rotation.x, tiltX, 0.1);
    droneGroup.children[0].rotation.z = THREE.MathUtils.lerp(droneGroup.children[0].rotation.z, tiltZ, 0.1);

    // 更新螺旋桨旋转
    propellers.forEach(prop => {
        prop.rotation.y += prop.userData.speed;
    });

    // 更新遥测数据
    updateTelemetry();
}

function updateTelemetry() {
    document.getElementById('altitude').textContent = droneState.position.y.toFixed(1);
    document.getElementById('speed').textContent = droneState.velocity.length().toFixed(1);
    document.getElementById('position').textContent = 
        `${droneState.position.x.toFixed(1)}, ${droneState.position.y.toFixed(1)}, ${droneState.position.z.toFixed(1)}`;
    
    const deg = (rad) => (rad * 180 / Math.PI).toFixed(0);
    document.getElementById('attitude').textContent = 
        `${deg(droneState.rotation.x)}°, ${deg(droneState.rotation.y)}°, ${deg(droneState.rotation.z)}°`;
}

function animate() {
    requestAnimationFrame(animate);
    
    updateDrone();
    controls.update();
    renderer.render(scene, camera);
}

// 启动
init();
