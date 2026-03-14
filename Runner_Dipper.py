import pygame
import random
import math
from sys import exit
from PIL import Image, ImageSequence

LARGURA, ALTURA      = 1300, 580
CHAO_Y               = 500
FPS                  = 60
GRAVIDADE_NORMAL     = 0.10
GRAVIDADE_PLANANDO   = 0.18
GRAVIDADE_QUEDA_FAST = 1
VEL_QUEDA_MAX        = 16
FORCA_PULO_BASE      = -18
FORCA_PULO_MAX       = -20
VEL_BASE             = 6
VEL_INCREMENTO       = 0.002
VEL_MAX              = 20
BONUS_PONTOS         = 15
GAP_MINIMO           = 120

SPAWN_MIN_X          = 200

ESTADO_INICIO    = 'inicio'
ESTADO_JOGANDO   = 'jogando'
ESTADO_TRANSICAO = 'transicao'
ESTADO_GAMEOVER  = 'gameover'

pygame.init()
screen = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption('Dipper Runner!')
clock  = pygame.time.Clock()

font_titulo  = pygame.font.Font('Font/fonte.ttf', 72)
font_grande  = pygame.font.Font('Font/fonte.ttf', 60)
font_media   = pygame.font.Font('Font/fonte.ttf', 44)
font_pequena = pygame.font.Font('Font/fonte.ttf', 32)
font_mini    = pygame.font.Font('Font/fonte.ttf', 26)

fundo_base = pygame.image.load('Graphics/Fundo/background.jpg').convert()
bg_far  = pygame.transform.scale(fundo_base, (LARGURA, ALTURA))
bg_mid  = pygame.transform.scale(fundo_base, (LARGURA, ALTURA))
bg_near = pygame.transform.scale(fundo_base, (LARGURA, ALTURA))

chao      = pygame.image.load('Graphics/Fundo/chao.png').convert()
perdeu    = pygame.transform.scale(pygame.image.load('Graphics/Fundo/Perdeu.jpg').convert(), (LARGURA, ALTURA))
inicio_bg = pygame.transform.scale(pygame.image.load('Graphics/Fundo/Dipper_wallpaper.jpg').convert(), (LARGURA, ALTURA))

monstro1_img_d = pygame.transform.scale(pygame.image.load('Graphics/Personagens/gnomo_d.png').convert_alpha(), (110, 90))
monstro1_img_e = pygame.transform.scale(pygame.image.load('Graphics/Personagens/gnomo_e.png').convert_alpha(), (110, 90))
monstro1_img   = monstro1_img_d
monstro2_img   = pygame.transform.scale(pygame.image.load('Graphics/Personagens/Bill.png').convert_alpha(), (100, 100))

def carrega_gif_frames(filepath, size):
    frames = []
    try:
        pil_img = Image.open(filepath)
        for g_frame in ImageSequence.Iterator(pil_img):
            rg   = g_frame.convert("RGBA")
            data = rg.tobytes("raw", "RGBA")
            cf   = pygame.image.fromstring(data, rg.size, "RGBA")
            frames.append(pygame.transform.scale(cf, size))
    except Exception as e:
        print(f"Erro ao carregar GIF {filepath}: {e}")
    return frames if frames else [pygame.Surface(size, pygame.SRCALPHA)]

dipper_frames_run = carrega_gif_frames('Graphics/Personagens/DipperRunning.gif', (100, 150))
mabel_frames_glow = carrega_gif_frames('Graphics/Personagens/MabelShinning.gif', (100, 100))

player_img = dipper_frames_run[0] if dipper_frames_run else pygame.Surface((100, 150))
_mabel_raw = mabel_frames_glow[0] if mabel_frames_glow else pygame.Surface((100, 100))

dipper_masks = [pygame.mask.from_surface(f) for f in dipper_frames_run]
mabel_masks  = [pygame.mask.from_surface(f) for f in mabel_frames_glow]

dipper_frames_intro = [pygame.transform.scale(f, (70, 105)) for f in dipper_frames_run]
mabel_frames_intro  = [pygame.transform.scale(f, (60, 60))  for f in mabel_frames_glow]

monstro1_intro = pygame.transform.scale(monstro1_img, (88, 72))
monstro2_intro = pygame.transform.scale(monstro2_img, (80, 80))
mabel_hud      = pygame.transform.scale(_mabel_raw,   (32, 32))

GLOW_PAD    = 22
GLOW_LAYERS = 6

def gerar_glow(surf, pad, layers, cor=(255, 215, 0)):
    w, h = surf.get_size()
    dest = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
    for i in range(layers, 0, -1):
        escala = 1.0 + (i / layers) * (pad / max(w, h))
        nw, nh = int(w * escala), int(h * escala)
        alpha  = int(200 * (layers - i + 1) / (layers + 1))
        cam    = pygame.transform.smoothscale(surf, (nw, nh)).copy()
        ts     = pygame.Surface((nw, nh), pygame.SRCALPHA)
        ts.fill((*cor, alpha))
        cam.blit(ts, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        dest.blit(cam, (pad + (w - nw) // 2, pad + (h - nh) // 2))
    dest.blit(surf, (pad, pad))
    return dest

mabel_glow_surf       = gerar_glow(_mabel_raw,  GLOW_PAD, GLOW_LAYERS)
mabel_intro_glow_surf = gerar_glow(pygame.transform.scale(_mabel_raw, (60, 60)), GLOW_PAD, GLOW_LAYERS)

mask_monstro1_d = pygame.mask.from_surface(monstro1_img_d)
mask_monstro1_e = pygame.mask.from_surface(monstro1_img_e)
mask_monstro2   = pygame.mask.from_surface(monstro2_img)

overlay = pygame.Surface((LARGURA, ALTURA))
overlay.fill((0, 0, 0))

class Estrela:
    def __init__(self, forcado_x=None, forcado_y=None):
        self.reset(forcado_x, forcado_y)

    def reset(self, fx=None, fy=None):
        self.x   = fx if fx is not None else random.randint(0, LARGURA)
        self.y   = fy if fy is not None else random.randint(0, ALTURA)
        self.vx  = random.uniform(-1.5, 1.5)
        self.vy  = random.uniform(-2.5, -0.5)
        self.r   = random.randint(2, 5)
        self.cor = random.choice([
            (255, 220, 50), (255, 180, 60), (255, 255, 150),
            (200, 255, 200), (180, 200, 255)
        ])
        self.vida     = random.randint(60, 140)
        self.vida_max = self.vida

    def update(self):
        self.x    += self.vx
        self.y    += self.vy
        self.vy   += 0.04
        self.vida -= 1
        return self.vida > 0

    def draw(self, surf):
        alpha = int(255 * (self.vida / self.vida_max))
        s = pygame.Surface((self.r * 2, self.r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.cor, alpha), (self.r, self.r), self.r)
        surf.blit(s, (int(self.x) - self.r, int(self.y) - self.r))

estrelas_go: list[Estrela] = []

class Poeira:
    def __init__(self, x, y):
        self.x = x; self.y = y
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-4, -1)
        self.life = 30

    def update(self):
        self.x += self.vx; self.y += self.vy
        self.vy += 0.2; self.life -= 1

    def draw(self, screen):
        if self.life > 0:
            pygame.draw.circle(screen, (200, 200, 200), (int(self.x), int(self.y)), 3)

poeira = []

stars_menu = [[random.randint(0, LARGURA), random.randint(0, ALTURA), random.randint(1, 3)] for _ in range(40)]

def spawn_x_aleatorio(offset_extra=0):
    x_min = max(LARGURA + 50, SPAWN_MIN_X)
    return random.randint(x_min + offset_extra, x_min + 400 + offset_extra)

def forca_pulo_atual(velocidade):
    t = max(0.0, min(1.0, (velocidade - VEL_BASE) / max(VEL_MAX - VEL_BASE, 1)))
    return FORCA_PULO_BASE + t * (FORCA_PULO_MAX - FORCA_PULO_BASE)

def spawn_obstaculo_aleatorio(outro_rect=None, eh_aereo=False):
    alt = monstro2_img.get_height() if eh_aereo else monstro1_img.get_height()
    x   = spawn_x_aleatorio(200 if eh_aereo else 0)
    if not eh_aereo:
        return x, CHAO_Y

    ZONAS = [
        (190, 230, 2),
        (260, 320, 4),
        (360, 420, 3),
    ]
    pesos = [z[2] for z in ZONAS]
    zona  = random.choices(ZONAS, weights=pesos, k=1)[0]
    bill_bottom = random.randint(zona[0], zona[1])

    if outro_rect:
        topo_m1 = outro_rect.top
        if bill_bottom > topo_m1 - GAP_MINIMO:
            zonas_ok = [(a, b, p) for a, b, p in ZONAS if a <= topo_m1 - GAP_MINIMO]
            if not zonas_ok:
                return spawn_x_aleatorio(900), 230
            zona = random.choices(zonas_ok, weights=[z[2] for z in zonas_ok], k=1)[0]
            bill_bottom = random.randint(zona[0], min(zona[1], topo_m1 - GAP_MINIMO))

    return x, bill_bottom

def mask_collide(rect_a, mask_a, rect_b, mask_b):
    offset = (rect_b.x - rect_a.x, rect_b.y - rect_a.y)
    return mask_a.overlap(mask_b, offset) is not None

def desenha_texto_sombra(surface, texto, font, cor, pos, sombra_cor=(0, 0, 0), offset=2):
    surface.blit(font.render(texto, True, sombra_cor), (pos[0] + offset, pos[1] + offset))
    surface.blit(font.render(texto, True, cor), pos)

def pontuacao_total(s):
    return s['score'] + s['bonus']

def reset_game(record=0):
    m1x, m1b = spawn_obstaculo_aleatorio(eh_aereo=False)
    m2_ref    = pygame.Rect(0, 0, monstro1_img.get_width(), monstro1_img.get_height())
    m2_ref.bottom = m1b
    m2x, m2b  = spawn_obstaculo_aleatorio(outro_rect=m2_ref, eh_aereo=True)
    state = {
        'score': 0, 'bonus': 0, 'mabels_pegas': 0,
        'velocidade': VEL_BASE, 'player_vel': 0,
        'planando': False, 'jogo_ativo': True,
        'transicao': False, 'transicao_alpha': 0,
        'flash_bonus': 0, 'glow_phase': 0.0,
        'record': record,
        'bg_far_x': 0, 'bg_mid_x': 0, 'bg_near_x': 0,
        'camera_shake': 0, 'camera_offset': [0, 0],
    }
    state['player_rect']   = player_img.get_rect(midbottom=(250, CHAO_Y))
    state['monstro1_rect'] = monstro1_img.get_rect(bottomleft=(m1x, m1b))
    state['monstro2_rect'] = monstro2_img.get_rect(bottomleft=(m2x, m2b))
    state['mabel_rect']    = _mabel_raw.get_rect(
        bottomleft=(spawn_x_aleatorio(500), random.choice([260, 340, CHAO_Y]))
    )
    poeira.clear()
    return state

estado       = ESTADO_INICIO
s            = reset_game()
record       = 0
titulo_surf  = font_grande.render('Dipper Runner!', True, (30, 30, 30))

intro_phase       = 0.0
espaco_frame      = 0
gnomo_frame_timer = 0
dipper_gif_timer  = 0
dipper_frame_idx  = 0
mabel_gif_timer   = 0
mabel_frame_idx   = 0

go_alpha = 0
go_shake = 0

while True:
    clock.tick(FPS)
    intro_phase  = (intro_phase + 0.05) % (2 * math.pi)
    espaco_frame = (espaco_frame + 1) % 60
    gnomo_frame_timer += 1

    dipper_gif_timer += 1
    mabel_gif_timer  += 1

    if dipper_frames_run and dipper_gif_timer >= 4:
        dipper_gif_timer = 0
        dipper_frame_idx = (dipper_frame_idx + 1) % len(dipper_frames_run)

    if mabel_frames_glow and mabel_gif_timer >= 5:
        mabel_gif_timer = 0
        mabel_frame_idx = (mabel_frame_idx + 1) % len(mabel_frames_glow)

    atual_dipper = dipper_frames_run[dipper_frame_idx] if dipper_frames_run else player_img
    atual_mabel  = mabel_frames_glow[mabel_frame_idx]  if mabel_frames_glow else _mabel_raw

    mask_player = dipper_masks[dipper_frame_idx]
    mask_mabel  = mabel_masks[mabel_frame_idx]

    frame_atual_gnomo = monstro1_img_d if (gnomo_frame_timer // 15) % 2 == 0 else monstro1_img_e
    mask_atual_gnomo  = mask_monstro1_d if (gnomo_frame_timer // 15) % 2 == 0 else mask_monstro1_e
    gnomo_bounce_y    = int(abs(math.sin(gnomo_frame_timer * 0.15)) * 6)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); exit()

        if estado == ESTADO_INICIO:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                estado = ESTADO_JOGANDO
                s = reset_game(record=record)

        elif estado == ESTADO_JOGANDO:
            pode_pular = s['player_rect'].bottom >= CHAO_Y
            forca      = forca_pulo_atual(s['velocidade'])

            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if pode_pular:
                    s['player_vel'] = forca
                    for i in range(6):
                        poeira.append(Poeira(s['player_rect'].centerx, CHAO_Y))
                s['planando'] = True

            if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
                s['planando'] = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if s['player_rect'].collidepoint(event.pos) and pode_pular:
                    s['player_vel'] = forca
                    for i in range(6):
                        poeira.append(Poeira(s['player_rect'].centerx, CHAO_Y))

        elif estado == ESTADO_GAMEOVER:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                record = max(pontuacao_total(s), s['record'])
                s      = reset_game(record=record)
                estado = ESTADO_JOGANDO
                go_alpha = 0
                estrelas_go.clear()

    if estado == ESTADO_JOGANDO:
        teclas = pygame.key.get_pressed()
        s['planando'] = teclas[pygame.K_SPACE]

    # ── Tela de início ──
    if estado == ESTADO_INICIO:
        screen.blit(inicio_bg, (0, 0))

        for star in stars_menu:
            star[0] -= star[2]
            if star[0] < 0:
                star[0] = LARGURA
                star[1] = random.randint(0, ALTURA)
            pygame.draw.circle(screen, (255, 255, 255), (star[0], star[1]), star[2])

        painel_w, painel_h = LARGURA // 3, ALTURA
        painel = pygame.Surface((painel_w, painel_h), pygame.SRCALPHA)
        painel.fill((10, 10, 30, 220))
        pygame.draw.line(painel, (100, 180, 255, 180), (painel_w - 2, 0), (painel_w - 2, painel_h), 4)
        px = py = 0
        screen.blit(painel, (px, py))

        # Título
        titulo_y_off = int(math.sin(intro_phase) * 5)
        t_surf  = font_media.render('DIPPER RUNNER!', True, (255, 240, 80))
        ts_surf = font_media.render('DIPPER RUNNER!', True, (180, 100, 0))
        screen.blit(ts_surf, (px + painel_w // 2 - t_surf.get_width() // 2 + 3, py + 18 + titulo_y_off + 3))
        screen.blit(t_surf,  (px + painel_w // 2 - t_surf.get_width() // 2,     py + 18 + titulo_y_off))
        pygame.draw.line(screen, (100, 180, 255, 200), (px + 20, py + 76), (px + painel_w - 20, py + 76), 2)

        # Como jogar
        desenha_texto_sombra(screen, 'Como jogar:', font_pequena, (180, 220, 255), (px + 20, py + 88))

        # Dipper à esquerda — botão e textos à direita, sem sobreposição
        screen.blit(dipper_frames_intro[dipper_frame_idx], (px + 18, py + 128))

        pulsa     = espaco_frame < 30
        tecla_cor = (255, 255, 100) if pulsa else (200, 200, 200)
        tecla_brd = (255, 255,   0) if pulsa else (150, 150, 150)
        btn_x, btn_y = px + 100, py + 130
        pygame.draw.rect(screen, tecla_cor, (btn_x, btn_y, 120, 38), border_radius=7)
        pygame.draw.rect(screen, tecla_brd, (btn_x, btn_y, 120, 38), 2, border_radius=7)
        desenha_texto_sombra(screen, 'ESPAÇO', font_mini, (30, 30, 30), (btn_x + 12, btn_y + 7), offset=1)

        seta_y = py + 128 if pulsa else py + 136
        desenha_texto_sombra(screen, '^ Pular',           font_mini, (220, 220, 220), (btn_x + 130, seta_y))
        desenha_texto_sombra(screen, 'Segurar -> Planar',  font_mini, (180, 180, 255), (btn_x, py + 178))
        desenha_texto_sombra(screen, 'Soltar  -> Cair',    font_mini, (180, 255, 200), (btn_x, py + 208))

        pygame.draw.line(screen, (80, 80, 120), (px + 20, py + 248), (px + painel_w - 20, py + 248), 1)

        # Obstáculos
        desenha_texto_sombra(screen, 'Obstáculos:', font_pequena, (255, 120, 100), (px + 20, py + 258))
        gnomo_intro_surf = pygame.transform.scale(frame_atual_gnomo, (72, 58))
        screen.blit(gnomo_intro_surf, (px + 20, py + 300 - gnomo_bounce_y))
        desenha_texto_sombra(screen, 'Gnomo', font_mini, (220, 180, 180), (px + 100, py + 316))
        bill_intro_surf = pygame.transform.scale(monstro2_intro, (64, 64))
        screen.blit(bill_intro_surf, (px + 210, py + 296))
        desenha_texto_sombra(screen, 'Bill', font_mini, (220, 180, 180), (px + 282, py + 316))

        pygame.draw.line(screen, (80, 80, 120), (px + 20, py + 374), (px + painel_w - 20, py + 374), 1)

        # Bônus
        desenha_texto_sombra(screen, 'Bônus:', font_pequena, (255, 228, 50), (px + 20, py + 384))
        gi_alpha = int(130 + 125 * math.sin(intro_phase))
        mabel_mini_glow = pygame.transform.scale(mabel_intro_glow_surf, (74, 74))
        mabel_mini_glow.set_alpha(gi_alpha)
        screen.blit(mabel_mini_glow,                      (px + 18, py + 426 - 5))
        screen.blit(mabel_frames_intro[mabel_frame_idx],  (px + 22, py + 426))
        desenha_texto_sombra(screen, f'Mabel +{BONUS_PONTOS} pts', font_mini, (255, 228, 50), (px + 100, py + 446))

        if espaco_frame < 40:
            start_surf = font_mini.render('ESPAÇO para iniciar', True, (100, 255, 180))
            start_somb = font_mini.render('ESPAÇO para iniciar', True, (0, 80, 40))
            sy_btn = ALTURA - 36
            screen.blit(start_somb, (px + painel_w // 2 - start_surf.get_width() // 2 + 2, sy_btn + 2))
            screen.blit(start_surf, (px + painel_w // 2 - start_surf.get_width() // 2,     sy_btn))

    # ── Jogo ativo ──
    elif estado == ESTADO_JOGANDO:

        s['velocidade'] = min(s['velocidade'] + VEL_INCREMENTO, VEL_MAX)
        vel = int(s['velocidade'])

        s['bg_far_x']  -= vel * 0.2
        s['bg_mid_x']  -= vel * 0.5
        s['bg_near_x'] -= vel * 0.8

        if s['bg_far_x']  <= -LARGURA: s['bg_far_x']  = 0
        if s['bg_mid_x']  <= -LARGURA: s['bg_mid_x']  = 0
        if s['bg_near_x'] <= -LARGURA: s['bg_near_x'] = 0

        screen.blit(bg_far,  (s['bg_far_x'],  0)); screen.blit(bg_far,  (s['bg_far_x']  + LARGURA, 0))
        screen.blit(bg_mid,  (s['bg_mid_x'],  0)); screen.blit(bg_mid,  (s['bg_mid_x']  + LARGURA, 0))
        screen.blit(bg_near, (s['bg_near_x'], 0)); screen.blit(bg_near, (s['bg_near_x'] + LARGURA, 0))

        screen.blit(chao, (0, CHAO_Y))
        screen.blit(titulo_surf, (LARGURA // 2 - titulo_surf.get_width() // 2, 18))

        if s['camera_shake'] > 0:
            s['camera_offset'][0] = random.randint(-s['camera_shake'], s['camera_shake'])
            s['camera_offset'][1] = random.randint(-s['camera_shake'], s['camera_shake'])
            s['camera_shake'] -= 1
        else:
            s['camera_offset'] = [0, 0]
        cx, cy = s['camera_offset']

        s['monstro1_rect'].x -= vel
        if s['monstro1_rect'].right <= 0:
            nx, nb = spawn_obstaculo_aleatorio(eh_aereo=False)
            s['monstro1_rect'].left   = nx
            s['monstro1_rect'].bottom = nb
            s['score'] += 1
        screen.blit(frame_atual_gnomo, (s['monstro1_rect'].x + cx, s['monstro1_rect'].y + cy - gnomo_bounce_y))

        s['monstro2_rect'].x -= int(vel * 1.85)
        if s['monstro2_rect'].right <= 0:
            nx, nb = spawn_obstaculo_aleatorio(outro_rect=s['monstro1_rect'], eh_aereo=True)
            s['monstro2_rect'].left   = nx
            s['monstro2_rect'].bottom = nb
            s['score'] += 1
        screen.blit(monstro2_img, (s['monstro2_rect'].x + cx, s['monstro2_rect'].y + cy))

        s['glow_phase'] = (s['glow_phase'] + 0.07) % (2 * math.pi)
        ga = int(130 + 125 * math.sin(s['glow_phase']))
        mabel_glow_surf.set_alpha(ga)
        screen.blit(mabel_glow_surf, (s['mabel_rect'].x - GLOW_PAD + cx, s['mabel_rect'].y - GLOW_PAD + cy))
        screen.blit(atual_mabel,     (s['mabel_rect'].x + cx,            s['mabel_rect'].y + cy))

        s['mabel_rect'].x -= vel
        if s['mabel_rect'].right <= 0:
            s['mabel_rect'].left   = spawn_x_aleatorio(500)
            s['mabel_rect'].bottom = random.choice([260, 340, CHAO_Y])

        no_ar    = s['player_rect'].bottom < CHAO_Y
        subindo  = s['player_vel'] < 0
        planando = s['planando'] and no_ar

        if planando:
            grav = GRAVIDADE_PLANANDO
            s['player_vel'] = min(s['player_vel'], 3.5)
        elif not no_ar or subindo:
            grav = GRAVIDADE_NORMAL
        else:
            grav = GRAVIDADE_QUEDA_FAST

        s['player_vel']    = min(s['player_vel'] + grav, VEL_QUEDA_MAX)
        s['player_rect'].y += int(s['player_vel'])

        if s['player_rect'].top    < 10:      s['player_rect'].top    = 10;      s['player_vel'] = 0
        if s['player_rect'].bottom >= CHAO_Y: s['player_rect'].bottom = CHAO_Y;  s['player_vel'] = 0

        screen.blit(atual_dipper, s['player_rect'].topleft)

        for p in poeira:
            p.update(); p.draw(screen)
        poeira[:] = [p for p in poeira if p.life > 0]

        pontos = pontuacao_total(s)
        hud_bg = pygame.Surface((295, 120), pygame.SRCALPHA)
        hud_bg.fill((0, 0, 0, 135))
        screen.blit(hud_bg, (8, 8))
        desenha_texto_sombra(screen, f'Score: {pontos}',           font_media,   (255, 255, 255), (18, 13))
        desenha_texto_sombra(screen, f'Vel: {s["velocidade"]:.1f}', font_pequena, (200, 200, 200), (18, 60))
        screen.blit(mabel_hud, (18, 85))
        desenha_texto_sombra(screen, f'x {s["mabels_pegas"]}', font_pequena, (255, 228, 50), (57, 89))
        rec_surf = font_pequena.render(f'Recorde: {s["record"]}', True, (220, 220, 100))
        screen.blit(rec_surf, (LARGURA - rec_surf.get_width() - 14, 14))

        if planando:
            p_surf = font_mini.render('~~ planando ~~', True, (180, 230, 255))
            p_surf.set_alpha(180)
            screen.blit(p_surf, (s['player_rect'].centerx - p_surf.get_width() // 2, s['player_rect'].top - 28))

        if s['flash_bonus'] > 0:
            fa = min(255, s['flash_bonus'] * 9)
            fs = font_media.render(f'+{BONUS_PONTOS}!', True, (255, 228, 0))
            fs.set_alpha(fa)
            screen.blit(fs, (s['player_rect'].centerx - 30, s['player_rect'].top - 55))
            s['flash_bonus'] -= 1

        if mask_collide(s['player_rect'], mask_player, s['monstro1_rect'], mask_atual_gnomo) or \
           mask_collide(s['player_rect'], mask_player, s['monstro2_rect'], mask_monstro2):
            estado               = ESTADO_TRANSICAO
            s['jogo_ativo']      = False
            s['transicao_alpha'] = 0
            s['camera_shake']    = 20

        if mask_collide(s['player_rect'], mask_player, s['mabel_rect'], mask_mabel):
            s['bonus']        += BONUS_PONTOS
            s['mabels_pegas'] += 1
            s['flash_bonus']   = 32
            s['mabel_rect'].left   = spawn_x_aleatorio(500)
            s['mabel_rect'].bottom = random.choice([260, 340, CHAO_Y])

    # ── Transição ──
    elif estado == ESTADO_TRANSICAO:
        screen.blit(bg_far,  (s['bg_far_x'],  0)); screen.blit(bg_far,  (s['bg_far_x']  + LARGURA, 0))
        screen.blit(bg_mid,  (s['bg_mid_x'],  0)); screen.blit(bg_mid,  (s['bg_mid_x']  + LARGURA, 0))
        screen.blit(bg_near, (s['bg_near_x'], 0)); screen.blit(bg_near, (s['bg_near_x'] + LARGURA, 0))
        screen.blit(chao, (0, CHAO_Y))

        if s['camera_shake'] > 0:
            s['camera_offset'][0] = random.randint(-s['camera_shake'], s['camera_shake'])
            s['camera_offset'][1] = random.randint(-s['camera_shake'], s['camera_shake'])
            s['camera_shake'] -= 1
        else:
            s['camera_offset'] = [0, 0]
        cx, cy = s['camera_offset']

        screen.blit(frame_atual_gnomo, (s['monstro1_rect'].x + cx, s['monstro1_rect'].y + cy - gnomo_bounce_y))
        screen.blit(monstro2_img,      (s['monstro2_rect'].x + cx, s['monstro2_rect'].y + cy))
        screen.blit(atual_mabel,       (s['mabel_rect'].x    + cx, s['mabel_rect'].y    + cy))
        screen.blit(atual_dipper,      s['player_rect'].topleft)

        s['transicao_alpha'] = min(255, s['transicao_alpha'] + 6)
        overlay.set_alpha(s['transicao_alpha'])
        screen.blit(overlay, (0, 0))

        if s['transicao_alpha'] >= 255:
            estado   = ESTADO_GAMEOVER
            go_alpha = 0
            go_shake = 20
            estrelas_go.clear()
            ecx, ecy = LARGURA // 2, ALTURA // 2
            for _ in range(80):
                e = Estrela(forcado_x=ecx + random.randint(-40, 40), forcado_y=ecy + random.randint(-40, 40))
                e.vx = random.uniform(-4, 4)
                e.vy = random.uniform(-5, -0.5)
                estrelas_go.append(e)

    # ── Game over ──
    elif estado == ESTADO_GAMEOVER:
        screen.blit(perdeu, (0, 0))
        esc = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        esc.fill((0, 0, 0, 140))
        screen.blit(esc, (0, 0))

        estrelas_go = [e for e in estrelas_go if e.update()]
        for e in estrelas_go:
            e.draw(screen)
        if random.random() < 0.3:
            e = Estrela(forcado_x=LARGURA // 2 + random.randint(-200, 200),
                        forcado_y=ALTURA  // 2 + random.randint(-80,  80))
            e.vx = random.uniform(-2, 2)
            e.vy = random.uniform(-2, -0.3)
            estrelas_go.append(e)

        go_alpha = min(255, go_alpha + 8)
        pontos   = pontuacao_total(s)
        novo_rec = pontos >= s['record'] and pontos > 0

        pw, ph = 600, 440
        pan = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pan.fill((10, 5, 20, 210))
        borda_cor = (255, 215, 0) if novo_rec else (200, 60, 60)
        pygame.draw.rect(pan, (*borda_cor, 230), pan.get_rect(), 3, border_radius=20)
        pan.set_alpha(go_alpha)
        panx = LARGURA // 2 - pw // 2
        pany = ALTURA  // 2 - ph // 2

        sx = sy = 0
        if go_shake > 0:
            sx = random.randint(-go_shake // 2, go_shake // 2)
            sy = random.randint(-go_shake // 2, go_shake // 2)
            go_shake = max(0, go_shake - 1)

        screen.blit(pan, (panx + sx, pany + sy))

        go_surf   = font_grande.render('GAME OVER', True, (255, 70, 70))
        go_sombra = font_grande.render('GAME OVER', True, (120,  0,  0))
        gox = LARGURA // 2 - go_surf.get_width() // 2
        goy = pany + 30
        go_surf.set_alpha(go_alpha); go_sombra.set_alpha(go_alpha)
        screen.blit(go_sombra, (gox + 4 + sx, goy + 4 + sy))
        screen.blit(go_surf,   (gox     + sx, goy     + sy))

        lw = 420
        lin = pygame.Surface((lw, 3), pygame.SRCALPHA)
        lin.fill((*borda_cor, go_alpha))
        screen.blit(lin, (LARGURA // 2 - lw // 2 + sx, pany + 105 + sy))

        sc_surf = font_media.render(f'Score Final:  {pontos}', True, (255, 255, 255))
        sc_surf.set_alpha(go_alpha)
        screen.blit(sc_surf, (LARGURA // 2 - sc_surf.get_width() // 2 + sx, pany + 125 + sy))

        if s['mabels_pegas'] > 0:
            mi = pygame.transform.scale(atual_mabel, (40, 40))
            mi.set_alpha(go_alpha)
            mx, my = LARGURA // 2 - 130, pany + 185
            screen.blit(mi, (mx + sx, my + sy))
            mb = font_pequena.render(f'x {s["mabels_pegas"]}   +{s["bonus"]} pts bônus', True, (255, 220, 60))
            mb.set_alpha(go_alpha)
            screen.blit(mb, (mx + 50 + sx, my + 4 + sy))

        if novo_rec:
            rec_phase = (pygame.time.get_ticks() / 400) % (2 * math.pi)
            rec_a     = int(180 + 75 * math.sin(rec_phase))
            rec_glow  = font_media.render('★  NOVO RECORDE!  ★', True, (255, 200, 0))
            rec_glow.set_alpha(min(go_alpha, rec_a))
            screen.blit(rec_glow, (LARGURA // 2 - rec_glow.get_width() // 2 + sx, pany + 250 + sy))
        else:
            r_surf = font_pequena.render(f'Recorde: {s["record"]}', True, (180, 180, 220))
            r_surf.set_alpha(go_alpha)
            screen.blit(r_surf, (LARGURA // 2 - r_surf.get_width() // 2 + sx, pany + 260 + sy))

        detalhe = font_mini.render(
            f'Obstáculos desviados: {s["score"]}   |   Mabels: {s["mabels_pegas"]}',
            True, (140, 140, 180)
        )
        detalhe.set_alpha(go_alpha)
        screen.blit(detalhe, (LARGURA // 2 - detalhe.get_width() // 2 + sx, pany + 330 + sy))

        if (pygame.time.get_ticks() // 500) % 2 == 0:
            bt   = font_pequena.render('   ESPAÇO para jogar novamente', True, (100, 255, 160))
            bt_s = font_pequena.render('   ESPAÇO para jogar novamente', True, (  0,  80,  40))
            bt.set_alpha(go_alpha); bt_s.set_alpha(go_alpha)
            bx = LARGURA // 2 - bt.get_width() // 2
            by = pany + 380
            screen.blit(bt_s, (bx + 2 + sx, by + 2 + sy))
            screen.blit(bt,   (bx     + sx, by     + sy))

    pygame.display.update()