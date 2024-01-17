import pygame
from sys import exit

pygame.init()
screen = pygame.display.set_mode((1300,580))
pygame.display.set_caption('Corre corre')
clock = pygame.time.Clock()
test_font = pygame.font.Font('Font/font.ttf', 50)

# Background
fundo = pygame.image.load('Graphics/background.jpg').convert()
chao = pygame.image.load('Graphics/chao.png').convert()

# Textos
Titulo = test_font.render('Meu primeiro jogo', False, 'Black')
Score = test_font.render('Score:', False, 'Black')
Score_rect = Score.get_rect(center = (470,130))

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

        if event.type == pygame.MOUSEBUTTONDOWN:
            if player_rect.collidepoint(event.pos):
                player_gravidade = -20
        
        if event.type == pygame.KEYDOWN:   # Apenas quando esta segurando o botao
            if event.key == pygame.K_SPACE:
                player_gravidade = -20     #  Sempre que apertar subira 20 px
 



    screen.blit(fundo,(0,0))
    screen.blit(chao,(0,500))
    screen.blit(Titulo,(330,50))
    screen.blit(Score, Score_rect)

    monstro1_rect.x -= 10
    if monstro1_rect.right <= 0: monstro1_rect.left = 1300
    screen.blit(monstro1 , monstro1_rect)

    player_gravidade += 1
    player_rect.y += player_gravidade 
    if player_rect.bottom >= 500:
        player_rect.bottom = 500
    screen.blit(player ,player_rect)
    
    pygame.display.update()
    clock.tick(60)