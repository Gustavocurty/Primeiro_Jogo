import pygame
import random
import math
from sys import exit
from PIL import Image, ImageSequence

# ─────────────────────────────────────────────
#  CONSTANTES
# ─────────────────────────────────────────────
LARGURA, ALTURA      = 1300, 580
CHAO_Y               = 500
FPS                  = 60
GRAVIDADE_NORMAL     = 1.1    # gravidade ao subir / queda rápida (solto espaço)
GRAVIDADE_PLANANDO   = 0.28   # gravidade reduzida ao segurar espaço no ar
GRAVIDADE_QUEDA_FAST = 2.2    # gravidade ao soltar espaço enquanto desce
VEL_QUEDA_MAX        = 18     # velocidade máxima de queda
FORCA_PULO_BASE      = -20
FORCA_PULO_MAX       = -28
VEL_BASE             = 6
VEL_INCREMENTO       = 0.002
VEL_MAX              = 20
BONUS_PONTOS         = 15
GAP_MINIMO           = 175    # gap vertical mínimo entre obstáculos (jogador=150px)

# Distância mínima de spawn à direita do jogador (3× largura do Dipper = 3×100 = 300)
DIPPER_LARGURA       = 100
SPAWN_MIN_X          = 250 + DIPPER_LARGURA * 3   # posX dipper + 3 larguras

# ─────────────────────────────────────────────
#  ESTADOS DO JOGO
# ─────────────────────────────────────────────
ESTADO_INICIO    = 'inicio'
ESTADO_JOGANDO   = 'jogando'
ESTADO_TRANSICAO = 'transicao'
ESTADO_GAMEOVER  = 'gameover'

# ─────────────────────────────────────────────
#  INICIALIZAÇÃO
# ─────────────────────────────────────────────
pygame.init()
screen = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption('Dipper Runner!')
clock  = pygame.time.Clock()

font_titulo  = pygame.font.Font('Font/font.ttf', 72)
font_grande  = pygame.font.Font('Font/font.ttf', 60)
font_media   = pygame.font.Font('Font/font.ttf', 40)
font_pequena = pygame.font.Font('Font/font.ttf', 28)
font_mini    = pygame.font.Font('Font/font.ttf', 22)

# ─────────────────────────────────────────────
#  ASSETS E PARALLAX
# ─────────────────────────────────────────────
fundo_base = pygame.image.load('Graphics/Fundo/background.jpg').convert()
# fundo = pygame.transform.scale(fundo_base, (LARGURA, ALTURA)) # Antigo fundo estático
bg_far = pygame.transform.scale(fundo_base, (LARGURA, ALTURA))
bg_mid = pygame.transform.scale(fundo_base, (LARGURA, ALTURA))
bg_near = pygame.transform.scale(fundo_base, (LARGURA, ALTURA))

chao   = pygame.image.load('Graphics/Fundo/chao.png').convert()
perdeu = pygame.transform.scale(
    pygame.image.load('Graphics/Fundo/Perdeu.jpg').convert(), (LARGURA, ALTURA)
)
inicio_bg = pygame.transform.scale(
    pygame.image.load('Graphics/Fundo/Dipper_wallpaper.jpg').convert(), (LARGURA, ALTURA)
)

monstro1_img_d = pygame.transform.scale(
    pygame.image.load('Graphics/Personagens/gnomo_d.png').convert_alpha(), (110, 90)
)
monstro1_img_e = pygame.transform.scale(
    pygame.image.load('Graphics/Personagens/gnomo_e.png').convert_alpha(), (110, 90)
)
monstro1_img = monstro1_img_d # imagem base/fallback
monstro2_img = pygame.transform.scale(
    pygame.image.load('Graphics/Personagens/Bill.png').convert_alpha(), (100, 100)
)
# ─────────────────────────────────────────────
#  FUNÇÃO PARA CARREGAR GIFS
# ─────────────────────────────────────────────
def carrega_gif_frames(filepath, size):
    frames = []
    try:
        pil_img = Image.open(filepath)
        for g_frame in ImageSequence.Iterator(pil_img):
            rg = g_frame.convert("RGBA")
            data = rg.tobytes("raw", "RGBA")
            cf = pygame.image.fromstring(data, rg.size, "RGBA")
            frames.append(pygame.transform.scale(sf, size))
    except Exception as e:
        print(f"Erro ao carregar GIF {filepath}: {e}")
    return frames if frames else [pygame.Surface(size)]  # Fallback

dipper_frames_run = carrega_gif_frames('Graphics/Personagens/DipperRunning.gif', (100, 150))
mabel_frames_glow = carrega_gif_frames('Graphics/Personagens/Mabel.png', (100, 100))

# Fallback inicial para não quebrar a lógica de retângulos/máscaras
player_img = dipper_frames_run[0] if dipper_frames_run else pygame.Surface((100, 150))
_mabel_raw = mabel_frames_glow[0] if mabel_frames_glow else pygame.Surface((100, 100))

# Versões para a tela de início (maiores, para apresentação)
monstro1_intro = pygame.transform.scale(monstro1_img, (88, 72))
monstro2_intro = pygame.transform.scale(monstro2_img, (80, 80))
mabel_intro    = pygame.transform.scale(_mabel_raw,   (80, 80))
player_intro   = pygame.transform.scale(player_img,   (70, 105))
mabel_hud      = pygame.transform.scale(_mabel_raw,   (32, 32))

# ─────────────────────────────────────────────
#  GLOW DOURADO DA MABEL (pré-camadas)
# ─────────────────────────────────────────────
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

# Geramos um glow apenas do primeiro frame para HUD e menus
mabel_glow_surf       = gerar_glow(_mabel_raw,   GLOW_PAD, GLOW_LAYERS)
mabel_intro_glow_surf = gerar_glow(mabel_intro, GLOW_PAD, GLOW_LAYERS)

# ─────────────────────────────────────────────
#  MÁSCARAS — pixel-perfect collision
# ─────────────────────────────────────────────
mask_player     = pygame.mask.from_surface(player_img)
mask_monstro1_d = pygame.mask.from_surface(monstro1_img_d)
mask_monstro1_e = pygame.mask.from_surface(monstro1_img_e)
mask_monstro2   = pygame.mask.from_surface(monstro2_img)
mask_mabel      = pygame.mask.from_surface(_mabel_raw)

# ─────────────────────────────────────────────
#  OVERLAY / PARTÍCULAS
# ─────────────────────────────────────────────
overlay = pygame.Surface((LARGURA, ALTURA))
overlay.fill((0, 0, 0))

# Partículas de estrela para tela de game over
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
        self.vida    = random.randint(60, 140)
        self.vida_max = self.vida

    def update(self):
        self.x    += self.vx
        self.y    += self.vy
        self.vy   += 0.04        # leve gravidade
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
        self.x = x
        self.y = y
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-4, -1)
        self.life = 30

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2
        self.life -= 1

    def draw(self, screen):
        if self.life > 0:
            pygame.draw.circle(screen, (200, 200, 200), (int(self.x), int(self.y)), 3)

poeira = []

stars_menu = []
for i in range(40):
    stars_menu.append([random.randint(0, LARGURA), random.randint(0, ALTURA), random.randint(1, 3)])


# ─────────────────────────────────────────────
#  FUNÇÕES AUXILIARES
# ─────────────────────────────────────────────

def spawn_x_aleatorio(offset_extra=0):
    """
    Nasce aleatoriamente entre 0 e 400px além da borda direita,
    sempre a pelo menos SPAWN_MIN_X px à direita do Dipper.
    """
    x_min = max(LARGURA + 50, SPAWN_MIN_X)
    return random.randint(x_min + offset_extra, x_min + 400 + offset_extra)


def forca_pulo_atual(velocidade):
    t = max(0.0, min(1.0, (velocidade - VEL_BASE) / max(VEL_MAX - VEL_BASE, 1)))
    return FORCA_PULO_BASE + t * (FORCA_PULO_MAX - FORCA_PULO_BASE)


def spawn_obstaculo_aleatorio(outro_rect=None, eh_aereo=False):
    """
    Retorna (left, bottom) para um obstáculo.
    - eh_aereo=False → nasce no chão (bottom=CHAO_Y) ou no ar.
    - eh_aereo=True  → usa spawn_monstro2_seguro lógica.
    Ambos respeitam GAP_MINIMO se outro_rect for passado.
    """
    alt = monstro2_img.get_height() if eh_aereo else monstro1_img.get_height()
    x   = spawn_x_aleatorio(200 if eh_aereo else 0)

    if not eh_aereo:
        # Monstro 1 pode nascer no chão ou levemente acima (para variedade futura)
        bottom = CHAO_Y
        return x, bottom

    # Monstro 2 (aéreo) — garante gap
    if outro_rect:
        topo_m1    = outro_rect.top
        bottom_max = topo_m1 - GAP_MINIMO
        bottom_min = alt + 60
        if bottom_max < bottom_min:
            return spawn_x_aleatorio(900), bottom_min
        return x, random.randint(bottom_min, bottom_max)

    return x, random.randint(alt + 60, CHAO_Y - GAP_MINIMO)


def mask_collide(rect_a, mask_a, rect_b, mask_b):
    offset = (rect_b.x - rect_a.x, rect_b.y - rect_a.y)
    return mask_a.overlap(mask_b, offset) is not None


def desenha_texto_sombra(surface, texto, font, cor, pos,
                          sombra_cor=(0, 0, 0), offset=2):
    surface.blit(font.render(texto, True, sombra_cor),
                 (pos[0] + offset, pos[1] + offset))
    surface.blit(font.render(texto, True, cor), pos)


def pontuacao_total(s):
    return s['score'] + s['bonus']


def reset_game(record=0):
    m1x, m1b = spawn_obstaculo_aleatorio(eh_aereo=False)
    m2_ref    = pygame.Rect(0, 0, monstro1_img.get_width(), monstro1_img.get_height())
    m2_ref.bottom = m1b
    m2x, m2b  = spawn_obstaculo_aleatorio(outro_rect=m2_ref, eh_aereo=True)

    state = {
        'score':           0,
        'bonus':           0,
        'mabels_pegas':    0,
        'velocidade':      VEL_BASE,
        'player_vel':      0,
        'planando':        False,   # True enquanto espaço pressionado no ar
        'jogo_ativo':      True,
        'transicao':       False,
        'transicao_alpha': 0,
        'flash_bonus':     0,
        'glow_phase':      0.0,
        'record':          record,
        'bg_far_x':        0,
        'bg_mid_x':        0,
        'bg_near_x':       0,
        'camera_shake':    0,
        'camera_offset':   [0, 0],
        'player_scale':    1.0
    }
    state['player_rect']   = player_img.get_rect(midbottom=(250, CHAO_Y))
    state['monstro1_rect'] = monstro1_img.get_rect(bottomleft=(m1x, m1b))
    state['monstro2_rect'] = monstro2_img.get_rect(bottomleft=(m2x, m2b))
    state['mabel_rect']    = _mabel_raw.get_rect(
        bottomleft=(spawn_x_aleatorio(500), random.choice([260, 340, CHAO_Y]))
    )
    poeira.clear()
    return state

# ─────────────────────────────────────────────
#  ESTADO GLOBAL
# ─────────────────────────────────────────────
estado    = ESTADO_INICIO
s         = reset_game()
record    = 0
titulo_surf = font_grande.render('Dipper Runner!', True, (30, 30, 30))

# Variáveis da tela de início
intro_phase   = 0.0   # para animações
espaco_frame  = 0     # animação do botão espaço
gnomo_frame_timer = 0 # para animar o gnomo

# Timers dos GIFs
dipper_gif_timer = 0
dipper_frame_idx = 0
mabel_gif_timer  = 0
mabel_frame_idx  = 0

# Variáveis tela game over
go_alpha      = 0     # fade-in do painel
go_shake      = 0     # frames de shake do "GAME OVER"

# ─────────────────────────────────────────────
#  LOOP PRINCIPAL
# ─────────────────────────────────────────────
while True:
    clock.tick(FPS)
    intro_phase  = (intro_phase + 0.05) % (2 * math.pi)
    espaco_frame = (espaco_frame + 1) % 60
    gnomo_frame_timer += 1

    # Atualiza GIFs
    dipper_gif_timer += 1
    mabel_gif_timer  += 1

    if dipper_frames_run and dipper_gif_timer >= 4:  # ~15 fps para Dipper
        dipper_gif_timer = 0
        dipper_frame_idx = (dipper_frame_idx + 1) % len(dipper_frames_run)
    
    if mabel_frames_glow and mabel_gif_timer >= 5:   # ~12 fps para Mabel
        mabel_gif_timer = 0
        mabel_frame_idx = (mabel_frame_idx + 1) % len(mabel_frames_glow)

    atual_dipper = dipper_frames_run[dipper_frame_idx] if dipper_frames_run else player_img
    atual_mabel  = mabel_frames_glow[mabel_frame_idx]  if mabel_frames_glow else _mabel_raw

    # Atualiza frame atual do gnomo a cada 15 ticks (mais lento)
    frame_atual_gnomo = monstro1_img_d if (gnomo_frame_timer // 15) % 2 == 0 else monstro1_img_e
    mask_atual_gnomo  = mask_monstro1_d if (gnomo_frame_timer // 15) % 2 == 0 else mask_monstro1_e
    # Pequeno pulinho natural (offset Y)
    gnomo_bounce_y = int(abs(math.sin(gnomo_frame_timer * 0.15)) * 6)

    # Atualiza máscaras
    mask_player = pygame.mask.from_surface(atual_dipper)
    mask_mabel  = pygame.mask.from_surface(atual_mabel)

    # ── Eventos ──────────────────────────────
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

        # INÍCIO
        if estado == ESTADO_INICIO:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                estado = ESTADO_JOGANDO
                s = reset_game(record=record)

        # JOGANDO
        elif estado == ESTADO_JOGANDO:
            pode_pular = s['player_rect'].bottom >= CHAO_Y
            forca      = forca_pulo_atual(s['velocidade'])

            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if pode_pular:
                    s['player_vel'] = forca
                    s['player_scale'] = 0.8
                    for i in range(6):
                        poeira.append(Poeira(s['player_rect'].centerx, CHAO_Y))
                s['planando'] = True   # começa a planar (mesmo que não esteja no ar ainda)

            if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
                s['planando'] = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if s['player_rect'].collidepoint(event.pos) and pode_pular:
                    s['player_vel'] = forca
                    s['player_scale'] = 0.8
                    for i in range(6):
                        poeira.append(Poeira(s['player_rect'].centerx, CHAO_Y))

        # GAME OVER
        elif estado == ESTADO_GAMEOVER:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                record = max(pontuacao_total(s), s['record'])
                s      = reset_game(record=record)
                estado = ESTADO_JOGANDO
                go_alpha = 0
                estrelas_go.clear()

    # Teclado contínuo para planar (segurando espaço)
    if estado == ESTADO_JOGANDO:
        teclas = pygame.key.get_pressed()
        s['planando'] = teclas[pygame.K_SPACE]

    # ══════════════════════════════════════════
    #  TELA DE INÍCIO
    # ══════════════════════════════════════════
    if estado == ESTADO_INICIO:
        screen.blit(inicio_bg, (0, 0)) # Fundo específico da tela de início (Dipper wallpaper)
        
        for star in stars_menu:
            star[0] -= star[2]
            if star[0] < 0:
                star[0] = LARGURA
                star[1] = random.randint(0,ALTURA)
            pygame.draw.circle(screen, (255,255,255), (star[0], star[1]), star[2])

        # ── Painel central alinhado à esquerda (1/3 da tela) ────────────────────
        painel_w, painel_h = LARGURA // 3, ALTURA
        painel = pygame.Surface((painel_w, painel_h), pygame.SRCALPHA)
        painel.fill((10, 10, 30, 220))
        # Borda luminosa só na direita
        pygame.draw.line(painel, (100, 180, 255, 180), (painel_w - 2, 0), (painel_w - 2, painel_h), 4)

        px = 0
        py = 0
        screen.blit(painel, (px, py))

        # ── Título ────────────────────────────
        titulo_y_off = int(math.sin(intro_phase) * 5)
        t_surf = font_media.render('DIPPER RUNNER!', True, (255, 240, 80)) # Fonte um pouco menor para caber
        ts_surf = font_media.render('DIPPER RUNNER!', True, (180, 100, 0))
        screen.blit(ts_surf, (px + painel_w // 2 - t_surf.get_width() // 2 + 3,
                               py + 30 + titulo_y_off + 3))
        screen.blit(t_surf,  (px + painel_w // 2 - t_surf.get_width() // 2,
                               py + 30 + titulo_y_off))

        # ── Linha divisória ───────────────────
        pygame.draw.line(screen, (100, 180, 255, 200),
                         (px + 20, py + 90), (px + painel_w - 20, py + 90), 2)

        # ── Como jogar ────────────────────────
        desenha_texto_sombra(screen, 'Como jogar:', font_pequena,
                             (180, 220, 255), (px + 20, py + 105))

        # Dipper caminhando (animado)
        dipper_intro_surf = pygame.transform.scale(atual_dipper, (70, 105))
        screen.blit(dipper_intro_surf, (px + 20, py + 145))

        # Tecla ESPAÇO animada
        pulsa = espaco_frame < 30
        tecla_cor   = (255, 255, 100) if pulsa else (200, 200, 200)
        tecla_borda = (255, 255, 0)   if pulsa else (150, 150, 150)
        pygame.draw.rect(screen, tecla_cor,   (px + 20, py + 155, 110, 38), border_radius=6)
        pygame.draw.rect(screen, tecla_borda, (px + 20, py + 155, 110, 38), 2, border_radius=6)
        desenha_texto_sombra(screen, 'ESPAÇO', font_mini,
                             (30, 30, 30), (px + 33, py + 164), sombra_cor=(0,0,0), offset=1)

        seta_y = py + 145 if pulsa else py + 155
        desenha_texto_sombra(screen, '^ Pular', font_mini,
                             (220, 220, 220), (px + 145, seta_y))
        desenha_texto_sombra(screen, 'Segurar -> Planar', font_mini,
                             (180, 180, 255), (px + 145, py + 175))
        desenha_texto_sombra(screen, 'Soltar -> Cair', font_mini,
                             (180, 255, 200), (px + 145, py + 195))

        # ── Linha divisória ───────────────────
        pygame.draw.line(screen, (80, 80, 120),
                         (px + 20, py + 235), (px + painel_w - 20, py + 235), 1)

        # ── Obstáculos ────────────────────────
        desenha_texto_sombra(screen, 'Obstáculos:', font_pequena,
                             (255, 120, 100), (px + 20, py + 245))

        # Gnomo
        gnomo_intro_surf = pygame.transform.scale(frame_atual_gnomo, (66, 54))
        screen.blit(gnomo_intro_surf, (px + 20, py + 285 - gnomo_bounce_y))
        desenha_texto_sombra(screen, 'Gnomo', font_mini,
                             (220, 180, 180), (px + 95, py + 300))

        # Bill
        bill_intro_surf = pygame.transform.scale(monstro2_intro, (60, 60))
        screen.blit(bill_intro_surf, (px + 200, py + 282))
        desenha_texto_sombra(screen, 'Bill', font_mini,
                             (220, 180, 180), (px + 270, py + 300))

        # ── Bônus ────────────────────────────
        pygame.draw.line(screen, (80, 80, 120),
                         (px + 20, py + 360), (px + painel_w - 20, py + 360), 1)

        desenha_texto_sombra(screen, 'Bônus:', font_pequena,
                             (255, 228, 50), (px + 20, py + 375))

        # Mabel com glow pulsante na tela de início
        gi_alpha = int(130 + 125 * math.sin(intro_phase))
        mabel_mini_glow = pygame.transform.scale(mabel_intro_glow_surf, (70, 70))
        mabel_mini = pygame.transform.scale(atual_mabel, (60, 60))
        
        mabel_mini_glow.set_alpha(gi_alpha)
        screen.blit(mabel_mini_glow, (px + 20, py + 415 - 5))
        screen.blit(mabel_mini, (px + 25, py + 415))
        desenha_texto_sombra(screen, f'Mabel +{BONUS_PONTOS} pts', font_mini,
                             (255, 228, 50), (px + 95, py + 435))

        # ── Botão iniciar (piscante) ──────────
        if espaco_frame < 40:
            start_surf = font_mini.render('ESPAÇO para iniciar', True, (100, 255, 180))
            start_somb = font_mini.render('ESPAÇO para iniciar', True, (0, 80, 40))
            sy = ALTURA - 40
            screen.blit(start_somb, (px + painel_w // 2 - start_surf.get_width() // 2 + 2, sy + 2))
            screen.blit(start_surf, (px + painel_w // 2 - start_surf.get_width() // 2, sy))

    # ══════════════════════════════════════════
    #  JOGO ATIVO
    # ══════════════════════════════════════════
    elif estado == ESTADO_JOGANDO:

        # ── Velocidade ────────────────────────
        s['velocidade'] = min(s['velocidade'] + VEL_INCREMENTO, VEL_MAX)
        vel = int(s['velocidade'])

        # ── Parallax Background ────────────────
        s['bg_far_x'] -= vel * 0.2
        s['bg_mid_x'] -= vel * 0.5
        s['bg_near_x'] -= vel * 0.8

        if s['bg_far_x'] <= -LARGURA:
            s['bg_far_x'] = 0
        if s['bg_mid_x'] <= -LARGURA:
            s['bg_mid_x'] = 0
        if s['bg_near_x'] <= -LARGURA:
            s['bg_near_x'] = 0

        screen.blit(bg_far, (s['bg_far_x'], 0))
        screen.blit(bg_far, (s['bg_far_x'] + LARGURA, 0))

        screen.blit(bg_mid, (s['bg_mid_x'], 0))
        screen.blit(bg_mid, (s['bg_mid_x'] + LARGURA, 0))

        screen.blit(bg_near, (s['bg_near_x'], 0))
        screen.blit(bg_near, (s['bg_near_x'] + LARGURA, 0))

        screen.blit(chao,  (0, CHAO_Y))
        screen.blit(titulo_surf,
                    (LARGURA // 2 - titulo_surf.get_width() // 2, 18))

        # ── Camera Shake ────────────────────────
        if s['camera_shake'] > 0:
            s['camera_offset'][0] = random.randint(-s['camera_shake'], s['camera_shake'])
            s['camera_offset'][1] = random.randint(-s['camera_shake'], s['camera_shake'])
            s['camera_shake'] -= 1
        else:
            s['camera_offset'] = [0, 0]

        cx, cy = s['camera_offset'][0], s['camera_offset'][1]

        # ── Monstro 1 ─────────────────────────
        s['monstro1_rect'].x -= vel
        if s['monstro1_rect'].right <= 0:
            nx, nb = spawn_obstaculo_aleatorio(eh_aereo=False)
            s['monstro1_rect'].left   = nx
            s['monstro1_rect'].bottom = nb
            s['score'] += 1
        screen.blit(frame_atual_gnomo, (s['monstro1_rect'].x + cx, s['monstro1_rect'].y + cy - gnomo_bounce_y))

        # ── Monstro 2 (Bill — mais rápido) ────────
        s['monstro2_rect'].x -= int(vel * 1.85)  # Bill voa 1.5x mais rápido
        if s['monstro2_rect'].right <= 0:
            nx, nb = spawn_obstaculo_aleatorio(outro_rect=s['monstro1_rect'], eh_aereo=True)
            s['monstro2_rect'].left   = nx
            s['monstro2_rect'].bottom = nb
            s['score'] += 1
        screen.blit(monstro2_img, (s['monstro2_rect'].x + cx, s['monstro2_rect'].y + cy))

        # ── Mabel ─────────────────────────────
        s['glow_phase'] = (s['glow_phase'] + 0.07) % (2 * math.pi)
        ga = int(130 + 125 * math.sin(s['glow_phase']))
        
        # Gerar glow dinâmico para a Mabel baseada no frame atual (só no jogo, é custoso)
        # Uma aproximação mais barata é desenhar um círculo ou o surf base do glow
        gf = mabel_glow_surf.copy() 
        gf.set_alpha(ga)
        screen.blit(gf,        (s['mabel_rect'].x - GLOW_PAD + cx, s['mabel_rect'].y - GLOW_PAD + cy))
        screen.blit(atual_mabel, (s['mabel_rect'].x + cx, s['mabel_rect'].y + cy))

        s['mabel_rect'].x -= vel
        if s['mabel_rect'].right <= 0:
            s['mabel_rect'].left   = spawn_x_aleatorio(500)
            s['mabel_rect'].bottom = random.choice([260, 340, CHAO_Y])

        # ── Física do jogador (pulo / plane / queda) ──
        no_ar     = s['player_rect'].bottom < CHAO_Y
        subindo   = s['player_vel'] < 0
        planando  = s['planando'] and no_ar

        if not no_ar:
            # No chão: gravidade normal
            grav = GRAVIDADE_NORMAL
        elif subindo:
            # Subindo: gravidade normal sempre (não interfere no arco de subida)
            grav = GRAVIDADE_NORMAL
            s['player_scale'] = min(s['player_scale'] + 0.02, 1.2)
        elif planando:
            # Descendo + espaço pressionado → plana suavemente
            grav = GRAVIDADE_PLANANDO
            # Limita velocidade de queda enquanto plana
            s['player_vel'] = min(s['player_vel'], 3.5)
        else:
            # Descendo + sem espaço → cai rápido
            grav = GRAVIDADE_QUEDA_FAST
            if s['player_vel'] > 5:
                s['player_scale'] = max(s['player_scale'] - 0.03, 0.85)

        s['player_vel'] = min(s['player_vel'] + grav, VEL_QUEDA_MAX)
        s['player_rect'].y += int(s['player_vel'])

        if s['player_rect'].top < 10:
            s['player_rect'].top = 10
            s['player_vel'] = 0
        if s['player_rect'].bottom >= CHAO_Y:
            s['player_rect'].bottom = CHAO_Y
            s['player_vel'] = 0
            s['player_scale'] = 1.0

        # Squash and Stretch render
        w_p = int(100 * s['player_scale'])
        h_p = int(150 / s['player_scale'])
        scaled_player = pygame.transform.scale(atual_dipper, (w_p, h_p))
        rect_p = scaled_player.get_rect(midbottom=s['player_rect'].midbottom)
        
        screen.blit(scaled_player, (rect_p.x + cx, rect_p.y + cy))

        # Poeira jump effect
        for p in poeira:
            p.update()
            p.draw(screen)
        poeira[:] = [p for p in poeira if p.life > 0]

        # ── HUD ───────────────────────────────
        pontos = pontuacao_total(s)
        hud_bg = pygame.Surface((295, 120), pygame.SRCALPHA)
        hud_bg.fill((0, 0, 0, 135))
        screen.blit(hud_bg, (8, 8))
        desenha_texto_sombra(screen, f'Score: {pontos}',
                             font_media, (255, 255, 255), (18, 13))
        desenha_texto_sombra(screen, f'Vel: {s["velocidade"]:.1f}',
                             font_pequena, (200, 200, 200), (18, 60))
        screen.blit(mabel_hud, (18, 85))
        desenha_texto_sombra(screen, f'x {s["mabels_pegas"]}',
                             font_pequena, (255, 228, 50), (57, 89))
        rec_surf = font_pequena.render(f'Recorde: {s["record"]}', True, (220, 220, 100))
        screen.blit(rec_surf, (LARGURA - rec_surf.get_width() - 14, 14))

        # Indicador visual de planar
        if planando:
            p_surf = font_mini.render('~~ planando ~~', True, (180, 230, 255))
            p_surf.set_alpha(180)
            screen.blit(p_surf, (s['player_rect'].centerx - p_surf.get_width() // 2,
                                  s['player_rect'].top - 28))

        # ── Flash bônus ───────────────────────
        if s['flash_bonus'] > 0:
            fa = min(255, s['flash_bonus'] * 9)
            fs = font_media.render(f'+{BONUS_PONTOS}!', True, (255, 228, 0))
            fs.set_alpha(fa)
            screen.blit(fs, (s['player_rect'].centerx - 30, s['player_rect'].top - 55))
            s['flash_bonus'] -= 1

        # ── Colisões ──────────────────────────
        if mask_collide(s['player_rect'], mask_player,
                        s['monstro1_rect'], mask_atual_gnomo) or \
           mask_collide(s['player_rect'], mask_player,
                        s['monstro2_rect'], mask_monstro2):
            estado           = ESTADO_TRANSICAO
            s['jogo_ativo']  = False
            s['transicao_alpha'] = 0
            s['camera_shake'] = 20

        if mask_collide(s['player_rect'], mask_player, s['mabel_rect'], mask_mabel):
            s['bonus']        += BONUS_PONTOS
            s['mabels_pegas'] += 1
            s['flash_bonus']   = 32
            s['mabel_rect'].left   = spawn_x_aleatorio(500)
            s['mabel_rect'].bottom = random.choice([260, 340, CHAO_Y])

    # ══════════════════════════════════════════
    #  TRANSIÇÃO
    # ══════════════════════════════════════════
    elif estado == ESTADO_TRANSICAO:
        # Fundo como ficou no momento da morte
        screen.blit(bg_far, (s['bg_far_x'], 0))
        screen.blit(bg_far, (s['bg_far_x'] + LARGURA, 0))
        screen.blit(bg_mid, (s['bg_mid_x'], 0))
        screen.blit(bg_mid, (s['bg_mid_x'] + LARGURA, 0))
        screen.blit(bg_near, (s['bg_near_x'], 0))
        screen.blit(bg_near, (s['bg_near_x'] + LARGURA, 0))
        
        screen.blit(chao,  (0, CHAO_Y))

        # Continua vibrando se ainda tiver s['camera_shake']
        if s['camera_shake'] > 0:
            s['camera_offset'][0] = random.randint(-s['camera_shake'], s['camera_shake'])
            s['camera_offset'][1] = random.randint(-s['camera_shake'], s['camera_shake'])
            s['camera_shake'] -= 1
        else:
            s['camera_offset'] = [0, 0]

        cx, cy = s['camera_offset'][0], s['camera_offset'][1]

        screen.blit(frame_atual_gnomo, (s['monstro1_rect'].x + cx, s['monstro1_rect'].y + cy - gnomo_bounce_y))
        screen.blit(monstro2_img, (s['monstro2_rect'].x + cx, s['monstro2_rect'].y + cy))
        screen.blit(atual_mabel,  (s['mabel_rect'].x + cx,    s['mabel_rect'].y + cy))
        
        # Mantém squash/stretch
        w_p = int(100 * s['player_scale'])
        h_p = int(150 / s['player_scale'])
        scaled_player = pygame.transform.scale(atual_dipper, (w_p, h_p))
        rect_p = scaled_player.get_rect(midbottom=s['player_rect'].midbottom)
        
        screen.blit(scaled_player, (rect_p.x + cx, rect_p.y + cy))

        s['transicao_alpha'] = min(255, s['transicao_alpha'] + 6)
        overlay.set_alpha(s['transicao_alpha'])
        screen.blit(overlay, (0, 0))

        if s['transicao_alpha'] >= 255:
            estado   = ESTADO_GAMEOVER
            go_alpha = 0
            go_shake = 20
            estrelas_go.clear()
            # Dispara partículas do centro da tela
            cx, cy = LARGURA // 2, ALTURA // 2
            for _ in range(80):
                e = Estrela(
                    forcado_x=cx + random.randint(-40, 40),
                    forcado_y=cy + random.randint(-40, 40)
                )
                e.vx = random.uniform(-4, 4)
                e.vy = random.uniform(-5, -0.5)
                estrelas_go.append(e)

    # ══════════════════════════════════════════
    #  GAME OVER
    # ══════════════════════════════════════════
    elif estado == ESTADO_GAMEOVER:
        # Fundo
        screen.blit(perdeu, (0, 0))

        # Overlay escuro para contraste
        esc = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        esc.fill((0, 0, 0, 140))
        screen.blit(esc, (0, 0))

        # Partículas
        estrelas_go = [e for e in estrelas_go if e.update()]
        for e in estrelas_go:
            e.draw(screen)
        # Reabastece partículas levemente
        if random.random() < 0.3:
            e = Estrela(
                forcado_x=LARGURA // 2 + random.randint(-200, 200),
                forcado_y=ALTURA  // 2 + random.randint(-80, 80)
            )
            e.vx = random.uniform(-2, 2)
            e.vy = random.uniform(-2, -0.3)
            estrelas_go.append(e)

        # Fade-in do painel
        go_alpha = min(255, go_alpha + 8)

        pontos   = pontuacao_total(s)
        novo_rec = pontos >= s['record'] and pontos > 0

        # ── Painel principal ──────────────────
        pw, ph = 600, 440
        pan = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pan.fill((10, 5, 20, 210))
        # Borda: dourada se novo recorde, vermelha se não
        borda_cor = (255, 215, 0) if novo_rec else (200, 60, 60)
        pygame.draw.rect(pan, (*borda_cor, 230), pan.get_rect(), 3, border_radius=20)
        pan.set_alpha(go_alpha)
        panx = LARGURA // 2 - pw // 2
        pany = ALTURA  // 2 - ph // 2

        # Shake nos primeiros frames
        sx, sy = 0, 0
        if go_shake > 0:
            sx = random.randint(-go_shake // 2, go_shake // 2)
            sy = random.randint(-go_shake // 2, go_shake // 2)
            go_shake = max(0, go_shake - 1)

        screen.blit(pan, (panx + sx, pany + sy))

        # ── "GAME OVER" com gradiente visual ─
        go_surf  = font_grande.render('GAME OVER', True, (255, 70, 70))
        go_sombra = font_grande.render('GAME OVER', True, (120, 0, 0))
        gox = LARGURA // 2 - go_surf.get_width()  // 2
        goy = pany + 30
        go_surf.set_alpha(go_alpha)
        go_sombra.set_alpha(go_alpha)
        screen.blit(go_sombra, (gox + 4 + sx, goy + 4 + sy))
        screen.blit(go_surf,   (gox     + sx, goy     + sy))

        # Linha decorativa sob o título
        lw  = 420
        lx  = LARGURA // 2 - lw // 2
        ly  = pany + 105
        lin = pygame.Surface((lw, 3), pygame.SRCALPHA)
        lin.fill((*borda_cor, go_alpha))
        screen.blit(lin, (lx + sx, ly + sy))

        # ── Score ─────────────────────────────
        sc_surf = font_media.render(f'Score Final:  {pontos}', True, (255, 255, 255))
        sc_surf.set_alpha(go_alpha)
        screen.blit(sc_surf, (LARGURA // 2 - sc_surf.get_width() // 2 + sx,
                               pany + 125 + sy))

        # ── Mabels resgatadas ─────────────────
        if s['mabels_pegas'] > 0:
            mi = pygame.transform.scale(atual_mabel, (40, 40))
            mi.set_alpha(go_alpha)
            mx = LARGURA // 2 - 130
            my = pany + 185
            screen.blit(mi, (mx + sx, my + sy))
            mb = font_pequena.render(
                f'x {s["mabels_pegas"]}   +{s["bonus"]} pts bônus',
                True, (255, 220, 60)
            )
            mb.set_alpha(go_alpha)
            screen.blit(mb, (mx + 50 + sx, my + 4 + sy))

        # ── Recorde ───────────────────────────
        if novo_rec:
            # Brilho dourado pulsante atrás do texto
            rec_phase = (pygame.time.get_ticks() / 400) % (2 * math.pi)
            rec_a     = int(180 + 75 * math.sin(rec_phase))
            rec_glow  = font_media.render('★  NOVO RECORDE!  ★', True, (255, 200, 0))
            rec_glow.set_alpha(min(go_alpha, rec_a))
            rx = LARGURA // 2 - rec_glow.get_width() // 2
            ry = pany + 250
            screen.blit(rec_glow, (rx + sx, ry + sy))
        else:
            r_surf = font_pequena.render(f'Recorde: {s["record"]}', True, (180, 180, 220))
            r_surf.set_alpha(go_alpha)
            screen.blit(r_surf, (LARGURA // 2 - r_surf.get_width() // 2 + sx,
                                  pany + 260 + sy))

        # ── Detalhe de pontuação ──────────────
        detalhe = font_mini.render(
            f'Obstáculos desviados: {s["score"]}   |   Mabels: {s["mabels_pegas"]}',
            True, (140, 140, 180)
        )
        detalhe.set_alpha(go_alpha)
        screen.blit(detalhe, (LARGURA // 2 - detalhe.get_width() // 2 + sx,
                               pany + 330 + sy))

        # ── Botão piscante ────────────────────
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            bt   = font_pequena.render('   ESPAÇO para jogar novamente', True, (100, 255, 160))
            bt_s = font_pequena.render('   ESPAÇO para jogar novamente', True, (0, 80, 40))
            bt.set_alpha(go_alpha)
            bt_s.set_alpha(go_alpha)
            bx = LARGURA // 2 - bt.get_width() // 2
            by = pany + 380
            screen.blit(bt_s, (bx + 2 + sx, by + 2 + sy))
            screen.blit(bt,   (bx + sx,      by + sy))

    pygame.display.update()