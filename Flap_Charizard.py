import pygame
import random
import math
from sys import exit
from PIL import Image, ImageSequence

# ─────────────────────────────────────────────
#  CONSTANTES
# ─────────────────────────────────────────────
LARGURA, ALTURA = 1300, 580
FPS             = 60

GRAVIDADE     = 0.55
VEL_QUEDA_MAX = 12
FORCA_PULO    = -10

# Limites verticais — sem chão, tela toda é área de jogo
LIMITE_TOPO   = 0
LIMITE_FUNDO  = ALTURA   # ao tocar o fundo, rebate para cima

HP_MAX        = 3
DANO_COOLDOWN = 90

VEL_INICIAL    = 7
VEL_MAX        = 20
VEL_INCREMENTO = 0.0015

GAP_INICIAL = 200
GAP_MINIMO  = 130
GAP_REDUCAO = 0.003

# Ciclo dia/noite: alterna a cada 30s de jogo, com 3s de crossfade
DURACAO_TEMA    = 30 * FPS   # frames por tema
DURACAO_FADE    = 3  * FPS   # frames de transição

ESTADO_INICIO   = 'inicio'
ESTADO_JOGANDO  = 'jogando'
ESTADO_GAMEOVER = 'gameover'

pygame.init()
screen = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption('Flappy Charizard!')
clock = pygame.time.Clock()

font_grande  = pygame.font.Font('Font/fonte.ttf', 60)
font_media   = pygame.font.Font('Font/fonte.ttf', 44)
font_pequena = pygame.font.Font('Font/fonte.ttf', 32)
font_mini    = pygame.font.Font('Font/fonte.ttf', 26)

# ─────────────────────────────────────────────
#  CARREGAMENTO SEGURO DE IMAGENS (fallback PIL)
# ─────────────────────────────────────────────
def carrega_imagem(filepath, alpha=False):
    try:
        img = pygame.image.load(filepath)
        return img.convert_alpha() if alpha else img.convert()
    except pygame.error:
        try:
            pil_img = Image.open(filepath).convert("RGBA")
            data    = pil_img.tobytes("raw", "RGBA")
            surf    = pygame.image.fromstring(data, pil_img.size, "RGBA")
            return surf.convert_alpha() if alpha else surf.convert()
        except Exception as e:
            print(f"Erro ao carregar {filepath}: {e}")
            s = pygame.Surface((100, 100))
            s.fill((200, 0, 200))
            return s

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

# ─────────────────────────────────────────────
#  ASSETS
# ─────────────────────────────────────────────
# Backgrounds dia e noite (cada um em 2 cópias para scroll infinito)
bg_dia_raw   = carrega_imagem('Graphics/Fundo/background_Dia_Flap.png')
bg_noite_raw = carrega_imagem('Graphics/Fundo/background_Noite_Flap.png')
bg_dia       = pygame.transform.scale(bg_dia_raw,   (LARGURA, ALTURA))
bg_noite     = pygame.transform.scale(bg_noite_raw, (LARGURA, ALTURA))

barreira_raw = carrega_imagem('Graphics/Fundo/Barreira.png', alpha=True)
BARREIRA_W   = 110

perdeu_bg = pygame.transform.scale(carrega_imagem('Graphics/Fundo/Perdeu.jpg'), (LARGURA, ALTURA))

# Charizard: 130×73
PLAYER_W, PLAYER_H = 130, 73
player_frames = carrega_gif_frames('Graphics/Personagens/Charizard.gif', (PLAYER_W, PLAYER_H))
if not player_frames:
    p_img = carrega_imagem('Graphics/Personagens/Charizard.png', alpha=True)
    player_frames = [pygame.transform.scale(p_img, (PLAYER_W, PLAYER_H))]

player_masks = [pygame.mask.from_surface(f) for f in player_frames]

# Barreira em tamanho fixo — a ponta fica no limite do gap,
# o restante ultrapassa a borda da tela (exatamente como Flappy Bird)
BARREIRA_W      = 110
BARREIRA_ALTURA = 420   # altura fixa da imagem escalada

barreira_normal  = pygame.transform.scale(barreira_raw, (BARREIRA_W, BARREIRA_ALTURA))
barreira_invertida = pygame.transform.flip(barreira_normal, False, True)

# Máscaras pré-calculadas (não mudam, reutilizadas em todas as instâncias)
mask_barreira_normal    = pygame.mask.from_surface(barreira_normal)
mask_barreira_invertida = pygame.mask.from_surface(barreira_invertida)

stars_menu = [[random.randint(0, LARGURA), random.randint(0, ALTURA), random.randint(1, 3)] for _ in range(50)]

# ─────────────────────────────────────────────
#  CLASSES
# ─────────────────────────────────────────────
class Barreira:
    """Par de barreiras com gap central em tamanho fixo.
    
    A borda que toca o gap é sempre a parte superior da imagem original:
    - Barreira de baixo: imagem normal, topo no início do gap inferior.
    - Barreira de cima: imagem invertida, borda inferior no final do gap superior
                        (imagem sai pelo topo da tela).
    """

    def __init__(self, x, gap):
        self.x      = x
        self.gap    = gap
        # gap_cy = centro vertical do gap; margens para não aparecer barreira vazia
        margem = int(gap // 2) + 30
        self.gap_cy = random.randint(margem, ALTURA - margem)
        self.passou = False
        self._calc_rects()

    def _calc_rects(self):
        topo_gap  = int(self.gap_cy - self.gap // 2)
        fundo_gap = int(self.gap_cy + self.gap // 2)

        self.y_top    = topo_gap - BARREIRA_ALTURA
        self.rect_top = pygame.Rect(self.x, self.y_top, BARREIRA_W, BARREIRA_ALTURA)

        self.y_bot    = fundo_gap
        self.rect_bot = pygame.Rect(self.x, self.y_bot, BARREIRA_W, BARREIRA_ALTURA)

    def update(self, vel):
        self.x         -= vel
        self.rect_top.x = self.x
        self.rect_bot.x = self.x

    def draw(self, surf, cx=0, cy=0):
        surf.blit(barreira_invertida, (self.rect_top.x + cx, self.rect_top.y + cy))
        surf.blit(barreira_normal,    (self.rect_bot.x + cx, self.rect_bot.y + cy))

    def collide(self, player_rect, player_mask):
        for rect, mask in [(self.rect_top, mask_barreira_invertida),
                           (self.rect_bot, mask_barreira_normal)]:
            offset = (rect.x - player_rect.x, rect.y - player_rect.y)
            if player_mask.overlap(mask, offset):
                return True
        return False

    @property
    def right(self):
        return self.x + BARREIRA_W


class Particula:
    def __init__(self, x, y, cor):
        self.x    = x; self.y = y
        self.vx   = random.uniform(-4, 4)
        self.vy   = random.uniform(-5, -1)
        self.cor  = cor
        self.life = random.randint(20, 40)
        self.r    = random.randint(2, 5)

    def update(self):
        self.x   += self.vx
        self.y   += self.vy
        self.vy  += 0.25
        self.life -= 1

    def draw(self, surf):
        if self.life > 0:
            pygame.draw.circle(surf, self.cor, (int(self.x), int(self.y)), self.r)


class Estrela:
    def __init__(self):
        self.x    = random.randint(0, LARGURA)
        self.y    = random.randint(0, ALTURA)
        self.vx   = random.uniform(-1, -0.3)
        self.r    = random.randint(1, 3)
        self.cor  = random.choice([(255,220,50),(255,180,60),(200,255,200),(180,200,255)])
        self.vida = random.randint(40, 100)
        self.vida_max = self.vida

    def update(self):
        self.x   += self.vx
        self.vida -= 1
        if self.x < 0 or self.vida <= 0:
            self.x    = LARGURA
            self.y    = random.randint(0, ALTURA)
            self.vida = self.vida_max

    def draw(self, surf):
        a = int(255 * self.vida / self.vida_max)
        s = pygame.Surface((self.r*2, self.r*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.cor, a), (self.r, self.r), self.r)
        surf.blit(s, (int(self.x)-self.r, int(self.y)-self.r))

go_estrelas = [Estrela() for _ in range(60)]

# ─────────────────────────────────────────────
#  FUNÇÕES AUXILIARES
# ─────────────────────────────────────────────
def desenha_texto_sombra(surface, texto, font, cor, pos, sombra_cor=(0,0,0), offset=2):
    surface.blit(font.render(texto, True, sombra_cor), (pos[0]+offset, pos[1]+offset))
    surface.blit(font.render(texto, True, cor), pos)

def desenha_hp(surface, hp, x, y):
    for i in range(HP_MAX):
        cor = (220, 40, 40) if i < hp else (80, 80, 80)
        pygame.draw.polygon(surface, cor, [
            (x+i*38+15, y+27), (x+i*38+2,  y+13), (x+i*38+2,  y+8),
            (x+i*38+7,  y+4),  (x+i*38+15, y+10), (x+i*38+23, y+4),
            (x+i*38+28, y+8),  (x+i*38+28, y+13),
        ])

def novo_gap(score):
    return max(GAP_MINIMO, GAP_INICIAL - score * GAP_REDUCAO)

def desenha_background(bg_x):
    """Desenha o background atual com crossfade dia/noite."""
    tema_frame = s.get('tema_frame', 0)
    fade_frame = s.get('tema_fade', 0)

    # Determina qual par de backgrounds mostrar e o alpha do fade
    ciclo    = tema_frame // DURACAO_TEMA
    eh_dia   = ciclo % 2 == 0   # par = dia, ímpar = noite
    em_fade  = tema_frame % DURACAO_TEMA >= (DURACAO_TEMA - DURACAO_FADE)

    bg_atual  = bg_dia   if eh_dia  else bg_noite
    bg_proximo = bg_noite if eh_dia else bg_dia

    # Desenha fundo atual (scroll)
    screen.blit(bg_atual,  (bg_x,          0))
    screen.blit(bg_atual,  (bg_x + LARGURA, 0))

    # Aplica crossfade para o próximo tema quando perto da transição
    if em_fade:
        frames_no_fade = tema_frame % DURACAO_TEMA - (DURACAO_TEMA - DURACAO_FADE)
        fade_alpha     = int(255 * frames_no_fade / DURACAO_FADE)
        fade_surf      = bg_proximo.copy()
        fade_surf.set_alpha(fade_alpha)
        screen.blit(fade_surf, (bg_x,          0))
        screen.blit(fade_surf, (bg_x + LARGURA, 0))

def reset_game(record=0):
    g = novo_gap(0)
    return {
        'player_vel':    0,
        'player_rect':   player_frames[0].get_rect(center=(250, ALTURA // 2)),
        'hp':            HP_MAX,
        'dano_cd':       0,
        'score':         0,
        'velocidade':    VEL_INICIAL,
        'barreiras':     [Barreira(LARGURA + 200, g), Barreira(LARGURA + 750, g)],
        'particulas':    [],
        'camera_shake':  0,
        'camera_offset': [0, 0],
        'flash_dano':    0,
        'bg_x':          0,
        'record':        record,
        'gif_timer':     0,
        'gif_idx':       0,
        'tema_frame':    0,   # contador geral para ciclo dia/noite
    }

# ─────────────────────────────────────────────
#  ESTADO GLOBAL
# ─────────────────────────────────────────────
estado       = ESTADO_INICIO
s            = reset_game()
record       = 0
intro_phase  = 0.0
espaco_frame = 0
bg_intro_x   = 0   # scroll independente na tela de início

# ─────────────────────────────────────────────
#  LOOP PRINCIPAL
# ─────────────────────────────────────────────
while True:
    clock.tick(FPS)
    intro_phase  = (intro_phase + 0.05) % (2 * math.pi)
    espaco_frame = (espaco_frame + 1) % 60

    if estado == ESTADO_JOGANDO:
        s['gif_timer'] += 1
        if s['gif_timer'] >= 5:
            s['gif_timer'] = 0
            s['gif_idx'] = (s['gif_idx'] + 1) % len(player_frames)
    atual_player = player_frames[s['gif_idx']]
    mask_player  = player_masks[s['gif_idx']]

    # ── Eventos ──────────────────────────────
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); exit()

        if estado == ESTADO_INICIO:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                estado = ESTADO_JOGANDO
                s = reset_game(record=record)

        elif estado == ESTADO_JOGANDO:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                s['player_vel'] = FORCA_PULO
            if event.type == pygame.MOUSEBUTTONDOWN:
                s['player_vel'] = FORCA_PULO

        elif estado == ESTADO_GAMEOVER:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                record = max(int(s['score']), record)
                s      = reset_game(record=record)
                estado = ESTADO_JOGANDO

    # ══════════════════════════════════════════
    #  TELA DE INÍCIO
    # ══════════════════════════════════════════
    if estado == ESTADO_INICIO:
        bg_intro_x -= 2
        if bg_intro_x <= -LARGURA: bg_intro_x = 0
        screen.blit(bg_dia, (bg_intro_x,          0))
        screen.blit(bg_dia, (bg_intro_x + LARGURA, 0))

        for star in stars_menu:
            star[0] -= star[2]
            if star[0] < 0:
                star[0] = LARGURA
                star[1] = random.randint(0, ALTURA)
            pygame.draw.circle(screen, (255, 255, 255), (star[0], star[1]), star[2])

        painel_w = 460
        painel = pygame.Surface((painel_w, ALTURA), pygame.SRCALPHA)
        painel.fill((10, 10, 30, 218))
        pygame.draw.line(painel, (100, 180, 255, 180), (painel_w-2, 0), (painel_w-2, ALTURA), 4)
        screen.blit(painel, (0, 0))

        titulo_y = int(math.sin(intro_phase) * 5) + 18
        t_surf  = font_media.render('FLAPPY CHARIZARD!', True, (255, 240, 80))
        ts_surf = font_media.render('FLAPPY CHARIZARD!', True, (180, 100, 0))
        tx = painel_w // 2 - t_surf.get_width() // 2
        screen.blit(ts_surf, (tx+3, titulo_y+3))
        screen.blit(t_surf,  (tx,   titulo_y))

        pygame.draw.line(screen, (100, 180, 255), (20, 76), (painel_w-20, 76), 2)

        p_intro = pygame.transform.scale(atual_player, (120, 67))
        bob_y   = int(math.sin(intro_phase * 1.5) * 7)
        screen.blit(p_intro, (painel_w // 2 - 60, 90 + bob_y))

        pygame.draw.line(screen, (80, 80, 120), (20, 175), (painel_w-20, 175), 1)
        desenha_texto_sombra(screen, 'Como jogar:', font_pequena, (180, 220, 255), (20, 185))

        pulsa     = espaco_frame < 30
        tecla_cor = (255, 255, 100) if pulsa else (200, 200, 200)
        tecla_brd = (255, 255,   0) if pulsa else (150, 150, 150)
        pygame.draw.rect(screen, tecla_cor, (20, 230, 130, 40), border_radius=7)
        pygame.draw.rect(screen, tecla_brd, (20, 230, 130, 40), 2, border_radius=7)
        desenha_texto_sombra(screen, 'ESPAÇO', font_mini, (30, 30, 30), (34, 239), offset=1)
        desenha_texto_sombra(screen, '→  Charizard sobe', font_mini, (220, 220, 220), (160, 239))

        desenha_texto_sombra(screen, 'Soltar → cai pela gravidade',  font_mini, (180, 255, 200), (20, 282))
        desenha_texto_sombra(screen, 'Clique repetido = voo contínuo', font_mini, (180, 200, 255), (20, 312))

        pygame.draw.line(screen, (80, 80, 120), (20, 350), (painel_w-20, 350), 1)
        desenha_texto_sombra(screen, 'Regras:', font_pequena, (255, 228, 50), (20, 360))
        desenha_texto_sombra(screen, '• Passe pelo espaço entre as barreiras', font_mini, (220, 220, 180), (20, 400))
        desenha_texto_sombra(screen, '• Bater = -1 vida  (3 vidas no total)',   font_mini, (255, 160, 160), (20, 428))
        desenha_texto_sombra(screen, '• Tocar o fundo da tela = dano',          font_mini, (255, 160, 160), (20, 456))
        desenha_texto_sombra(screen, '• Gap diminui com o tempo!',              font_mini, (200, 200, 200), (20, 484))

        if espaco_frame < 40:
            st = font_mini.render('ESPAÇO para iniciar', True, (100, 255, 180))
            ss = font_mini.render('ESPAÇO para iniciar', True, (0, 80, 40))
            sx = painel_w // 2 - st.get_width() // 2
            screen.blit(ss, (sx+2, ALTURA-36+2))
            screen.blit(st, (sx,   ALTURA-36))

    # ══════════════════════════════════════════
    #  JOGO ATIVO
    # ══════════════════════════════════════════
    elif estado == ESTADO_JOGANDO:

        s['velocidade'] = min(s['velocidade'] + VEL_INCREMENTO, VEL_MAX)
        vel = s['velocidade']

        # Avança contador do ciclo dia/noite
        s['tema_frame'] += 1

        # Scroll do background
        s['bg_x'] -= vel * 0.4
        if s['bg_x'] <= -LARGURA: s['bg_x'] = 0

        desenha_background(s['bg_x'])

        # Camera shake
        if s['camera_shake'] > 0:
            s['camera_offset'][0] = random.randint(-s['camera_shake'], s['camera_shake'])
            s['camera_offset'][1] = random.randint(-s['camera_shake'], s['camera_shake'])
            s['camera_shake'] -= 1
        else:
            s['camera_offset'] = [0, 0]
        cx, cy = s['camera_offset']

        # Barreiras
        x_mais_direita = max(b.x for b in s['barreiras'])
        for b in s['barreiras']:
            b.update(int(vel))
            b.draw(screen, cx, cy)
            if not b.passou and b.right < s['player_rect'].left:
                b.passou    = True
                s['score'] += 1

        s['barreiras'] = [b for b in s['barreiras'] if b.right > 0]
        while len(s['barreiras']) < 2:
            novo_x = x_mais_direita + random.randint(480, 640)
            s['barreiras'].append(Barreira(novo_x, novo_gap(s['score'])))
            x_mais_direita = novo_x

        # ── Física Flappy ──
        s['player_vel'] = min(s['player_vel'] + GRAVIDADE, VEL_QUEDA_MAX)
        s['player_rect'].y += int(s['player_vel'])

        # Limite topo: para o movimento
        if s['player_rect'].top < LIMITE_TOPO:
            s['player_rect'].top = LIMITE_TOPO
            s['player_vel'] = 0

        # Limite fundo: rebate para cima com dano
        if s['player_rect'].bottom >= LIMITE_FUNDO:
            s['player_rect'].bottom = LIMITE_FUNDO
            s['player_vel'] = FORCA_PULO * 0.6   # rebate suavemente para cima
            if s['dano_cd'] == 0:
                s['hp']          -= 1
                s['dano_cd']      = DANO_COOLDOWN
                s['flash_dano']   = 15
                s['camera_shake'] = 10
                for _ in range(14):
                    s['particulas'].append(Particula(
                        s['player_rect'].centerx, LIMITE_FUNDO - 10,
                        random.choice([(255,80,80),(255,160,0),(255,220,50)])
                    ))
                if s['hp'] <= 0:
                    estado = ESTADO_GAMEOVER

        if s['dano_cd']    > 0: s['dano_cd']    -= 1
        if s['flash_dano'] > 0:
            s['flash_dano'] -= 1
            fl = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            fl.fill((255, 0, 0, int(90 * s['flash_dano'] / 15)))
            screen.blit(fl, (0, 0))

        # Colisão com barreiras
        for b in s['barreiras']:
            if b.collide(s['player_rect'], mask_player) and s['dano_cd'] == 0:
                s['hp']          -= 1
                s['dano_cd']      = DANO_COOLDOWN
                s['flash_dano']   = 15
                s['camera_shake'] = 12
                for _ in range(20):
                    s['particulas'].append(Particula(
                        s['player_rect'].centerx, s['player_rect'].centery,
                        random.choice([(255,80,80),(255,160,0),(255,220,50),(255,255,80)])
                    ))
                if s['hp'] <= 0:
                    estado = ESTADO_GAMEOVER

        for p in s['particulas']:
            p.update(); p.draw(screen)
        s['particulas'] = [p for p in s['particulas'] if p.life > 0]

        if s['dano_cd'] == 0 or (s['dano_cd'] // 6) % 2 == 0:
            screen.blit(atual_player, (s['player_rect'].x + cx, s['player_rect'].y + cy))

        hud = pygame.Surface((310, 55), pygame.SRCALPHA)
        hud.fill((0, 0, 0, 130))
        screen.blit(hud, (8, 8))
        desenha_texto_sombra(screen, f'Score: {int(s["score"])}', font_media, (255, 255, 255), (18, 10))

        rec_s = font_pequena.render(f'Recorde: {record}', True, (220, 220, 100))
        screen.blit(rec_s, (LARGURA - rec_s.get_width() - 14, 14))

        desenha_hp(screen, s['hp'], 18, ALTURA - 52)

    # ══════════════════════════════════════════
    #  GAME OVER
    # ══════════════════════════════════════════
    elif estado == ESTADO_GAMEOVER:
        screen.blit(perdeu_bg, (0, 0))
        esc = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        esc.fill((0, 0, 0, 150))
        screen.blit(esc, (0, 0))

        for e in go_estrelas:
            e.update(); e.draw(screen)

        novo_rec  = int(s['score']) > record
        borda_cor = (255, 215, 0) if novo_rec else (200, 60, 60)

        pw, ph = 560, 400
        pan = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pan.fill((10, 5, 20, 215))
        pygame.draw.rect(pan, (*borda_cor, 230), pan.get_rect(), 3, border_radius=20)
        panx = LARGURA // 2 - pw // 2
        pany = ALTURA  // 2 - ph // 2
        screen.blit(pan, (panx, pany))

        go_s = font_grande.render('GAME OVER', True, (255, 70, 70))
        go_b = font_grande.render('GAME OVER', True, (120,  0,  0))
        gox  = LARGURA // 2 - go_s.get_width() // 2
        screen.blit(go_b, (gox+4, pany+26+4))
        screen.blit(go_s, (gox,   pany+26))

        lw = 420
        lin = pygame.Surface((lw, 3), pygame.SRCALPHA)
        lin.fill((*borda_cor, 220))
        screen.blit(lin, (LARGURA//2 - lw//2, pany + 103))

        sc_s = font_media.render(f'Score Final:  {int(s["score"])}', True, (255, 255, 255))
        screen.blit(sc_s, (LARGURA//2 - sc_s.get_width()//2, pany + 118))

        if novo_rec:
            rec_phase = (pygame.time.get_ticks() / 400) % (2 * math.pi)
            rec_a     = int(180 + 75 * math.sin(rec_phase))
            rec_g     = font_media.render('★  NOVO RECORDE!  ★', True, (255, 200, 0))
            rec_g.set_alpha(rec_a)
            screen.blit(rec_g, (LARGURA//2 - rec_g.get_width()//2, pany + 188))
        else:
            r_s = font_pequena.render(f'Recorde: {record}', True, (180, 180, 220))
            screen.blit(r_s, (LARGURA//2 - r_s.get_width()//2, pany + 198))

        hp_lbl = font_pequena.render('Vidas restantes:', True, (200, 200, 200))
        screen.blit(hp_lbl, (LARGURA//2 - hp_lbl.get_width()//2, pany + 256))
        desenha_hp(screen, max(s['hp'], 0), LARGURA//2 - 57, pany + 292)

        det = font_mini.render(
            f'Vel. final: {s["velocidade"]:.1f}   |   Gap: {int(novo_gap(s["score"]))}px',
            True, (140, 140, 180)
        )
        screen.blit(det, (LARGURA//2 - det.get_width()//2, pany + 342))

        if (pygame.time.get_ticks() // 500) % 2 == 0:
            bt   = font_pequena.render('ESPAÇO para jogar novamente', True, (100, 255, 160))
            bt_s = font_pequena.render('ESPAÇO para jogar novamente', True, (  0,  80,  40))
            bx   = LARGURA // 2 - bt.get_width() // 2
            screen.blit(bt_s, (bx+2, pany+364+2))
            screen.blit(bt,   (bx,   pany+364))

    pygame.display.update()