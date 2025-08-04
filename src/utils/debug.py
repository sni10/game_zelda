import pygame
from src.core.config_loader import get_color


pygame.init()
font = pygame.font.Font(None, 30)


def debug(info, y=10, x=10):
    display_surface = pygame.display.get_surface()
    debug_surface = font.render(str(info), True, get_color('WHITE'))
    debug_rectangle = debug_surface.get_rect(topleft=(x, y))
    pygame.draw.rect(display_surface, get_color('BLACK'), debug_rectangle)
    display_surface.blit(debug_surface, debug_rectangle)
