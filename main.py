from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

app = Ursina()

grass_texture = load_texture('assets/grass_block.png')
stone_texture = load_texture('assets/stone_block.png')
brick_texture = load_texture('assets/brick_block.png')
dirt_texture = load_texture('assets/dirt_block.png')
sky_texture = load_texture('assets/skybox.png')
arm_texture = load_texture('assets/arm_texture.png')
punch_sound = Audio('assets/punch_sound', loop=False, autoplay=False)

block_pick = 1
slot_size = 0.1
inventory_slots = []

def update_inventory_ui(selected_index):
    for i, slot in enumerate(inventory_slots):
        scale_factor = 1.2 if i == selected_index else 1.0
        offset = 0.05 if i == selected_index else 0.0
        slot.scale = (slot_size * scale_factor, slot_size * scale_factor)
        slot.position = Vec2(-0.5 + i * (slot_size + 0.05), -0.45 + offset)

def update():
    global block_pick

    if held_keys['left mouse'] or held_keys['right mouse']:
        hand.active()
    else:
        hand.passive()

    for i in range(5):
        if held_keys[str(i + 1)]:
            block_pick = i + 1
            update_inventory_ui(i)

    if block_pick == 5:
        return

class Voxel(Button):
    def __init__(self, position=(0, 0, 0), block_texture=grass_texture):
        super().__init__(
            parent=scene,
            position=position,
            model='assets/block',
            origin_y=0.5,
            texture=block_texture,
            color=color.hsv(0, 0, random.uniform(0.9, 1)),
            scale=0.5
        )

    def input(self, key):
        if self.hovered:
            if key == 'right mouse down' and block_pick != 5:
                punch_sound.play()
                block_textures = [grass_texture, stone_texture, brick_texture, dirt_texture]
                Voxel(position=self.position + mouse.normal, block_texture=block_textures[block_pick - 1])

            if key == 'left mouse down' and block_pick != 5:
                punch_sound.play()
                destroy(self)

class Sky(Entity):
    def __init__(self):
        super().__init__(
            parent=scene,
            model='sphere',
            texture=sky_texture,
            scale=150,
            double_sided=True
        )

class Hand(Entity):
    def __init__(self):
        super().__init__(
            parent=camera.ui,
            model='assets/arm',
            texture=arm_texture,
            scale=0.2,
            rotation=Vec3(150, -10, 0),
            position=Vec2(0.4, -0.6)
        )
        self._initial_position = self.position

    def active(self):
        self.position = Vec2(0.3, -0.5)

    def passive(self):
        self.position = self._initial_position

class Player(FirstPersonController):
    def __init__(self):
        super().__init__()

        self.slow_speed = 2.5

    def update(self):
        super().update()
        self.speed = self.slow_speed if held_keys['shift'] else 5
        if held_keys['escape']:
            application.quit()

        if held_keys['5']:
            self.attack()

    def attack(self):
        """Обрабатывает атаку моба."""
        if mob and distance(self.position, mob.position) <= 2:
            mob.knock_back(self, strength=2)


class Mob(Entity):
    def __init__(self, position=(0, 0, 0), target=None, scale=(1, 2, 1)):
        super().__init__(
            parent=scene,
            model='assets/village',
            position=position,
            scale=scale
        )
        self.speed = 1
        self.target = target
        self.collider = BoxCollider(self, center=(0.5, 1, 0.5), size=(1, 2, 1))
        self.min_distance = 1

    def update(self):
        # Обработка горизонтального движения
        if self.target:
            direction = self.target.position - self.position
            direction.y = 0  # Игнорируем высоту для горизонтального движения

            distance_to_target = direction.length()
            if distance_to_target > self.min_distance:
                if not self.is_colliding(direction):
                    self.position += direction.normalized() * self.speed * time.dt

            self.look_at(self.target.position)
            self.rotation_x = 0
            self.rotation_z = 0

    def is_colliding(self, direction):
        ray = boxcast(
            self.position + Vec3(0.5, 1, 0.5),  # Центр коллайдера
            direction=direction.normalized(),
            distance=self.speed,
            ignore=[self],
            thickness=(1, 2, 1)
        )
        return ray.hit

    def knock_back(self, source, strength=2):
        """Отталкивает моба от игрока."""
        direction = self.position - source.position
        direction.y = 0  # Игнорируем высоту для отталкивания
        self.position += direction.normalized() * strength
        print(f"Mob knocked back! New position: {self.position}")

def generate_world():
    width_world = 17
    width_world_half = (width_world - 1) / 2
    for z in range(width_world):
        for x in range(width_world):
            Voxel(position=(x - width_world_half, 0, z - width_world_half))

    layer_thickness = 2
    layers = [dirt_texture, stone_texture]
    for y_offset, texture in enumerate(layers):
        for z in range(width_world):
            for x in range(width_world):
                for layer in range(layer_thickness):
                    Voxel(position=(x - width_world_half, -1 - y_offset * layer_thickness - layer, z - width_world_half), block_texture=texture)

def create_inventory():
    textures = ["assets/grass_inv.PNG", "assets/stone_inv.PNG", "assets/brick_inv.PNG", "assets/dirt_inv.PNG", "assets/arm_texture.png"]
    for i, texture in enumerate(textures):
        slot = Entity(
            parent=camera.ui,
            model='cube',
            texture=texture,
            scale=(slot_size, slot_size),
            position=Vec2(-0.5 + i * (slot_size + 0.05), -0.45)
        )
        inventory_slots.append(slot)

player = Player()
mob = Mob(position=(5, 2, 1), target=player, scale=(0.002, 0.003, 0.002))
sky = Sky()
hand = Hand()
generate_world()
create_inventory()
update_inventory_ui(4)

app.run()
