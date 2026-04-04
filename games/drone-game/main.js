// 无人机躲避挑战游戏

// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', function() {
    initGame();
});

const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

// 游戏状态
const game = {
    running: false,
    score: 0,
    level: 1,
    lives: 3,
    speed: 3,
    obstacleSpeed: 3,
    spawnRate: 60,
    frameCount: 0
};

// 无人机
const drone = {
    x: 100,
    y: canvas.height / 2,
    width: 60,
    height: 40,
    velocityY: 0,
    velocityX: 0,
    speed: 8,
    friction: 0.9
};

// 障碍物数组
let obstacles = [];

// 按键状态
const keys = {
    up: false, down: false, left: false, right: false
};

// 云朵（装饰）
let clouds = [];

// 星星（装饰）
let stars = [];

// 初始化云朵
function initClouds() {
    clouds = [];
    for (let i = 0; i < 5; i++) {
        clouds.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height * 0.6,
            width: Math.random() * 100 + 50,
            speed: Math.random() * 0.5 + 0.2
        });
    }
}

// 初始化星星
function initStars() {
    stars = [];
    for (let i = 0; i < 30; i++) {
        stars.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height * 0.4,
            size: Math.random() * 2 + 1,
            twinkle: Math.random() * Math.PI * 2
        });
    }
}

// 重置游戏
function resetGame() {
    game.running = true;
    game.score = 0;
    game.level = 1;
    game.lives = 3;
    game.speed = 3;
    game.obstacleSpeed = 3;
    game.spawnRate = 60;
    game.frameCount = 0;
    
    drone.x = 100;
    drone.y = canvas.height / 2;
    drone.velocityX = 0;
    drone.velocityY = 0;
    
    obstacles = [];
    
    initClouds();
    initStars();
    
    updateUI();
    document.getElementById('startScreen').style.display = 'none';
    document.getElementById('gameOverScreen').style.display = 'none';
    
    gameLoop();
}

// 更新UI
function updateUI() {
    document.getElementById('scoreDisplay').textContent = game.score;
    document.getElementById('levelDisplay').textContent = game.level;
    document.getElementById('livesDisplay').textContent = '❤️'.repeat(game.lives);
}

// 创建障碍物
function createObstacle() {
    const types = ['building', 'bird', 'drone'];
    const type = types[Math.floor(Math.random() * types.length)];
    
    let obstacle = {
        x: canvas.width + 50,
        y: Math.random() * (canvas.height - 100) + 50,
        width: 40,
        height: 40,
        type: type
    };
    
    if (type === 'building') {
        obstacle.width = 50;
        obstacle.height = Math.random() * 200 + 100;
        obstacle.y = canvas.height - obstacle.height;
    } else if (type === 'bird') {
        obstacle.width = 30;
        obstacle.height = 20;
        obstacle.wingOffset = 0;
    } else if (type === 'drone') {
        obstacle.width = 40;
        obstacle.height = 30;
        obstacle.rotorOffset = 0;
    }
    
    obstacles.push(obstacle);
}

// 绘制背景
function drawBackground() {
    // 渐变天空
    const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
    gradient.addColorStop(0, '#0f0f23');
    gradient.addColorStop(0.5, '#1a1a3e');
    gradient.addColorStop(1, '#2a2a5e');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // 绘制星星
    stars.forEach(star => {
        star.twinkle += 0.05;
        const alpha = (Math.sin(star.twinkle) + 1) / 2 * 0.5 + 0.5;
        ctx.fillStyle = `rgba(255, 255, 255, ${alpha})`;
        ctx.beginPath();
        ctx.arc(star.x, star.y, star.size, 0, Math.PI * 2);
        ctx.fill();
    });
    
    // 绘制云朵
    ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
    clouds.forEach(cloud => {
        cloud.x -= cloud.speed;
        if (cloud.x < -cloud.width) {
            cloud.x = canvas.width + cloud.width;
            cloud.y = Math.random() * canvas.height * 0.6;
        }
        ctx.beginPath();
        ctx.ellipse(cloud.x, cloud.y, cloud.width, cloud.width / 3, 0, 0, Math.PI * 2);
        ctx.fill();
    });
    
    // 绘制地面
    ctx.fillStyle = '#1a1a2e';
    ctx.fillRect(0, canvas.height - 30, canvas.width, 30);
    
    // 绘制网格线（模拟透视）
    ctx.strokeStyle = 'rgba(0, 212, 255, 0.1)';
    ctx.lineWidth = 1;
    for (let i = 0; i < 20; i++) {
        const y = canvas.height - 30 - i * 30;
        if (y < 0) break;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
    }
}

// 绘制无人机
function drawDrone() {
    ctx.save();
    ctx.translate(drone.x, drone.y);
    
    // 添加倾斜效果
    const tiltX = drone.velocityY * 0.02;
    const tiltZ = -drone.velocityX * 0.02;
    ctx.rotate(tiltZ);
    
    // 机身
    ctx.fillStyle = '#333';
    ctx.beginPath();
    ctx.ellipse(0, 0, drone.width / 2, drone.height / 4, 0, 0, Math.PI * 2);
    ctx.fill();
    
    // 机臂
    ctx.strokeStyle = '#444';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(-20, -10);
    ctx.lineTo(-30, -25);
    ctx.moveTo(20, -10);
    ctx.lineTo(30, -25);
    ctx.moveTo(-20, 10);
    ctx.lineTo(-30, 25);
    ctx.moveTo(20, 10);
    ctx.lineTo(30, 25);
    ctx.stroke();
    
    // 螺旋桨
    ctx.fillStyle = 'rgba(0, 212, 255, 0.5)';
    const rotorOffset = Math.sin(game.frameCount * 0.5) * 5;
    ctx.beginPath();
    ctx.ellipse(-30, -25 + rotorOffset, 15, 4, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(30, -25 - rotorOffset, 15, 4, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(-30, 25 - rotorOffset, 15, 4, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(30, 25 + rotorOffset, 15, 4, 0, 0, Math.PI * 2);
    ctx.fill();
    
    // 云台相机
    ctx.fillStyle = '#222';
    ctx.beginPath();
    ctx.arc(15, 5, 8, 0, Math.PI * 2);
    ctx.fill();
    
    // 相机镜头
    ctx.fillStyle = '#00ff88';
    ctx.beginPath();
    ctx.arc(20, 5, 4, 0, Math.PI * 2);
    ctx.fill();
    
    // LED灯
    ctx.fillStyle = '#ff0000';
    ctx.beginPath();
    ctx.arc(-25, 0, 3, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#00ff00';
    ctx.beginPath();
    ctx.arc(25, 0, 3, 0, Math.PI * 2);
    ctx.fill();
    
    ctx.restore();
}

// 绘制障碍物
function drawObstacles() {
    obstacles.forEach(obs => {
        if (obs.type === 'building') {
            // 建筑物
            ctx.fillStyle = '#4444aa';
            ctx.fillRect(obs.x, obs.y, obs.width, obs.height);
            
            // 窗户
            ctx.fillStyle = 'rgba(255, 255, 100, 0.3)';
            for (let row = 0; row < Math.floor(obs.height / 30); row++) {
                for (let col = 0; col < 3; col++) {
                    if (Math.random() > 0.3) {
                        ctx.fillRect(obs.x + 8 + col * 15, obs.y + 10 + row * 30, 10, 15);
                    }
                }
            }
        } else if (obs.type === 'bird') {
            // 鸟
            obs.wingOffset += 0.2;
            const wingY = Math.sin(obs.wingOffset) * 10;
            
            ctx.fillStyle = '#8B4513';
            ctx.beginPath();
            ctx.ellipse(obs.x, obs.y, obs.width / 2, obs.height / 2, 0, 0, Math.PI * 2);
            ctx.fill();
            
            // 翅膀
            ctx.strokeStyle = '#8B4513';
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.moveTo(obs.x - 5, obs.y);
            ctx.lineTo(obs.x - 20, obs.y - wingY);
            ctx.moveTo(obs.x + 5, obs.y);
            ctx.lineTo(obs.x + 20, obs.y - wingY);
            ctx.stroke();
            
            // 眼睛
            ctx.fillStyle = '#fff';
            ctx.beginPath();
            ctx.arc(obs.x + 10, obs.y - 3, 3, 0, Math.PI * 2);
            ctx.fill();
        } else if (obs.type === 'drone') {
            // 敌方无人机
            ctx.save();
            ctx.translate(obs.x, obs.y);
            
            // 机身
            ctx.fillStyle = '#aa3333';
            ctx.beginPath();
            ctx.ellipse(0, 0, 20, 10, 0, 0, Math.PI * 2);
            ctx.fill();
            
            // 机臂
            ctx.strokeStyle = '#aa3333';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(-15, -5);
            ctx.lineTo(-25, -15);
            ctx.moveTo(15, -5);
            ctx.lineTo(25, -15);
            ctx.moveTo(-15, 5);
            ctx.lineTo(-25, 15);
            ctx.moveTo(15, 5);
            ctx.lineTo(25, 15);
            ctx.stroke();
            
            // 螺旋桨
            obs.rotorOffset += 0.3;
            const rotor = Math.sin(obs.rotorOffset) * 3;
            ctx.fillStyle = 'rgba(255, 100, 100, 0.5)';
            ctx.beginPath();
            ctx.ellipse(-25, -15 + rotor, 10, 3, 0, 0, Math.PI * 2);
            ctx.fill();
            ctx.beginPath();
            ctx.ellipse(25, -15 - rotor, 10, 3, 0, 0, Math.PI * 2);
            ctx.fill();
            ctx.beginPath();
            ctx.ellipse(-25, 15 - rotor, 10, 3, 0, 0, Math.PI * 2);
            ctx.fill();
            ctx.beginPath();
            ctx.ellipse(25, 15 + rotor, 10, 3, 0, 0, Math.PI * 2);
            ctx.fill();
            
            // 红眼
            ctx.fillStyle = '#ff0000';
            ctx.beginPath();
            ctx.arc(-8, 0, 3, 0, Math.PI * 2);
            ctx.fill();
            ctx.beginPath();
            ctx.arc(8, 0, 3, 0, Math.PI * 2);
            ctx.fill();
            
            ctx.restore();
        }
    });
}

// 碰撞检测
function checkCollision() {
    const droneBox = {
        x: drone.x - drone.width / 2,
        y: drone.y - drone.height / 2,
        width: drone.width,
        height: drone.height
    };
    
    for (let obs of obstacles) {
        const obsBox = {
            x: obs.x - obs.width / 2,
            y: obs.y - obs.height / 2,
            width: obs.width,
            height: obs.height
        };
        
        if (obs.type === 'building') {
            obsBox.x = obs.x;
            obsBox.y = obs.y;
        }
        
        if (droneBox.x < obsBox.x + obsBox.width &&
            droneBox.x + droneBox.width > obsBox.x &&
            droneBox.y < obsBox.y + obsBox.height &&
            droneBox.y + droneBox.height > obsBox.y) {
            return true;
        }
    }
    return false;
}

// 更新游戏状态
function update() {
    if (!game.running) return;
    
    game.frameCount++;
    
    // 更新分数
    game.score += 1;
    
    // 根据分数增加难度
    if (game.score % 500 === 0) {
        game.level++;
        game.obstacleSpeed += 0.5;
        game.spawnRate = Math.max(20, game.spawnRate - 5);
    }
    
    // 移动无人机
    if (keys.up) drone.velocityY -= drone.speed * 0.1;
    if (keys.down) drone.velocityY += drone.speed * 0.1;
    if (keys.left) drone.velocityX -= drone.speed * 0.1;
    if (keys.right) drone.velocityX += drone.speed * 0.1;
    
    drone.velocityX *= drone.friction;
    drone.velocityY *= drone.friction;
    
    drone.x += drone.velocityX;
    drone.y += drone.velocityY;
    
    // 边界限制
    drone.x = Math.max(drone.width / 2, Math.min(canvas.width - drone.width / 2, drone.x));
    drone.y = Math.max(drone.height / 2, Math.min(canvas.height - drone.height / 2 - 30, drone.y));
    
    // 生成障碍物
    if (game.frameCount % game.spawnRate === 0) {
        createObstacle();
    }
    
    // 移动障碍物
    obstacles.forEach(obs => {
        obs.x -= game.obstacleSpeed;
        if (obs.type === 'bird') {
            obs.y += Math.sin(obs.wingOffset * 0.5) * 2;
        }
    });
    
    // 移除离开屏幕的障碍物
    obstacles = obstacles.filter(obs => obs.x > -100);
    
    // 碰撞检测
    if (checkCollision()) {
        game.lives--;
        obstacles = obstacles.filter(obs => obs.x < canvas.width);
        
        if (game.lives <= 0) {
            gameOver();
        } else {
            // 短暂无敌
            drone.x = 100;
            drone.y = canvas.height / 2;
            drone.velocityX = 0;
            drone.velocityY = 0;
        }
    }
    
    updateUI();
}

// 游戏结束
function gameOver() {
    game.running = false;
    document.getElementById('finalScore').textContent = game.score;
    document.getElementById('gameOverScreen').style.display = 'flex';
}

// 绘制
function draw() {
    drawBackground();
    drawObstacles();
    drawDrone();
}

// 游戏循环
function gameLoop() {
    if (!game.running) return;

    update();
    draw();

    requestAnimationFrame(gameLoop);
}

// 重置游戏
function resetGame() {
    game.running = true;
    game.score = 0;
    game.level = 1;
    game.lives = 3;
    game.speed = 3;
    game.obstacleSpeed = 3;
    game.spawnRate = 60;
    game.frameCount = 0;

    drone.x = 100;
    drone.y = canvas.height / 2;
    drone.velocityX = 0;
    drone.velocityY = 0;

    obstacles = [];

    initClouds();
    initStars();

    updateUI();
    document.getElementById('startScreen').style.display = 'none';
    document.getElementById('gameOverScreen').style.display = 'none';

    gameLoop();
}

// 初始化游戏
function initGame() {
    // 事件监听
    document.addEventListener('keydown', (e) => {
        switch (e.key) {
            case 'ArrowUp':
            case 'w':
            case 'W':
                keys.up = true;
                e.preventDefault();
                break;
            case 'ArrowDown':
            case 's':
            case 'S':
                keys.down = true;
                e.preventDefault();
                break;
            case 'ArrowLeft':
            case 'a':
            case 'A':
                keys.left = true;
                e.preventDefault();
                break;
            case 'ArrowRight':
            case 'd':
            case 'D':
                keys.right = true;
                e.preventDefault();
                break;
        }
    });

    document.addEventListener('keyup', (e) => {
        switch (e.key) {
            case 'ArrowUp':
            case 'w':
            case 'W':
                keys.up = false;
                break;
            case 'ArrowDown':
            case 's':
            case 'S':
                keys.down = false;
                break;
            case 'ArrowLeft':
            case 'a':
            case 'A':
                keys.left = false;
                break;
            case 'ArrowRight':
            case 'd':
            case 'D':
                keys.right = false;
                break;
        }
    });

    document.getElementById('startBtn').addEventListener('click', resetGame);
    document.getElementById('restartBtn').addEventListener('click', resetGame);

    // 初始化
    initClouds();
    initStars();
    draw();
}
