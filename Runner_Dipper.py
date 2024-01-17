import pygame
from sys import exit

def Pontos():
    Tempo_de_Jogo = int(pygame.time.get_ticks()/1500) - TempoTot    # /1000 para ficar em segundos, e nao em milisegundos
    Score = test_font.render(f'Score: {Tempo_de_Jogo}', False, 'Black')
    Score_Rect = Score.get_rect(center = (600,130))
    screen.blit(Score, Score_Rect)
    return Tempo_de_Jogo

pygame.init()
screen = pygame.display.set_mode((1300,580))
pygame.display.set_caption('Corre corre')
clock = pygame.time.Clock()
test_font = pygame.font.Font('Font/font.ttf', 50)
Jogo_Ativo = True
TempoTot = 0
Score = 0

# Background
fundo = pygame.image.load('Graphics/Fundo/background.jpg').convert()
chao = pygame.image.load('Graphics/Fundo/chao.png').convert()
perdeu = pygame.image.load('Graphics/Fundo/Perdeu.jpg').convert()
perdeu = pygame.transform.scale(perdeu, (1300, 800))

# Textos
Titulo = test_font.render('Meu primeiro jogo', False, 'Black')
Recomecar = test_font.render('Aperte ESPACO para recomecar..', False, 'White')

# Personagens - Monstros
monstro1 = pygame.image.load('Graphics/Personagens/gnomo.png').convert_alpha()
monstro1 = pygame.transform.scale(monstro1, (110, 90))    # Diminuir o tamanho da imagem
monstro1_rect = monstro1.get_rect(bottomright = (800,500))

# Personagens principal
player = pygame.image.load('Graphics/Personagens/dipper.png').convert_alpha()
player = pygame.transform.scale(player, (100, 150))    # Diminuir o tamanho da imagem
player_rect = player.get_rect(midbottom = (250,500))
player_gravidade = 0


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

        if Jogo_Ativo:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if player_rect.collidepoint(event.pos) and player_rect.bottom >= 500:
                    player_gravidade = -20
        
            if event.type == pygame.KEYDOWN:   # Apenas quando esta segurando o botao
                if event.key == pygame.K_SPACE and player_rect.bottom >= 500:
                    player_gravidade = -20     #  Sempre que apertar subira 20 px
        else:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE: 
                Jogo_Ativo = True  # Quando o jogo estiver acabado, de apertar ESPAÇO Retornara
                monstro1_rect.left = 800  # Levara o monstro para o lugar dele
                TempoTot = int(pygame.time.get_ticks()/1500)

    if Jogo_Ativo:
        # Background
        screen.blit(fundo,(0,0))
        screen.blit(chao,(0,500))
        screen.blit(Titulo,(400,50))
        Score = Pontos()

        Pontos()


        # Personagem - Monstro
        monstro1_rect.x -= 10
        if monstro1_rect.right <= 0: 
            monstro1_rect.left = 1300
        screen.blit(monstro1 , monstro1_rect)

        # Personagem princiapl
        player_gravidade += 1
        player_rect.y += player_gravidade 
        if player_rect.bottom >= 500:
            player_rect.bottom = 500
        screen.blit(player ,player_rect)

        # Colisao
        if monstro1_rect.colliderect(player_rect):
            Jogo_Ativo = False 

    else:   # O que aparecerá se o usuário perder o jogo
        screen.blit(perdeu,(0,0))
        screen.blit(Recomecar,(500,500))

        # Texto do Score - Game Over
        Texto_Score = test_font.render(f'Seu Score: {Score}', False, 'White')
        Texto_Score_rect = Texto_Score.get_rect(center = (1130, 170))
        screen.blit(Texto_Score, Texto_Score_rect)

    pygame.display.update()
    clock.tick(60)