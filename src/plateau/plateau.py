from __future__ import annotations

import pygame
from enum import Enum
from plateau.case import Case, ResultatTir
from navires.bateau import Bateau, Alignement, DirectionDeplacement


class ResultatDeplacement(Enum):
    DEPLACE = "DEPLACE"
    BLOQUE = "BLOQUE"
    INVALIDE = "INVALIDE"


class Plateau:
    NB_LIGNES = 22
    NB_COLONNES = 22

    def __init__(self, x_loc=55, y_loc=160, cell_width=16):
        self.x_loc = x_loc
        self.y_loc = y_loc
        self.cell_width = cell_width
        self.grid_size_w = self.NB_COLONNES * self.cell_width
        self.grid_size_h = self.NB_LIGNES * self.cell_width
        self.rect = pygame.Rect(x_loc, y_loc, self.grid_size_w, self.grid_size_h)
        self.surface = pygame.Surface((self.grid_size_w, self.grid_size_h))
        self.casesImportantes: list[Case] = []
        self.bateaux: list[Bateau] = []
        self.cells: list[Case] = []
        self.initialiserGrille()

    def initialiserGrille(self) -> None:
        self.cells = []
        for ligne in range(self.NB_LIGNES):
            for colonne in range(self.NB_COLONNES):
                x = self.x_loc + colonne * self.cell_width
                y = self.y_loc + ligne * self.cell_width
                self.cells.append(Case(ligne, colonne, x, y, self.cell_width))
        self.draw_grid()

    def draw_grid(self, window_surface: pygame.Surface | None = None, font: pygame.font.Font | None = None):
        self.surface.fill((60, 145, 235))

        for i in range(self.NB_COLONNES + 1):
            x = i * self.cell_width
            pygame.draw.line(self.surface, (0, 0, 0), (x, 0), (x, self.grid_size_h), 1)

        for i in range(self.NB_LIGNES + 1):
            y = i * self.cell_width
            pygame.draw.line(self.surface, (0, 0, 0), (0, y), (self.grid_size_w, y), 1)

        if window_surface is not None:
            window_surface.blit(self.surface, (self.x_loc, self.y_loc))
            if font is not None:
                for j in range(self.NB_LIGNES):
                    lettre = chr(65 + j)
                    txt = font.render(lettre, True, (0, 0, 0))
                    rect = txt.get_rect(center=(self.x_loc - 20, self.y_loc + j * self.cell_width + self.cell_width // 2))
                    window_surface.blit(txt, rect)

                for i in range(self.NB_COLONNES):
                    chiffre = str(i + 1)
                    txt = font.render(chiffre, True, (0, 0, 0))
                    rect = txt.get_rect(center=(self.x_loc + i * self.cell_width + self.cell_width // 2, self.y_loc - 15))
                    window_surface.blit(txt, rect)

    def estDansGrille(self, ligne: int, colonne: int) -> bool:
        return 0 <= ligne < self.NB_LIGNES and 0 <= colonne < self.NB_COLONNES

    def getCase(self, ligne: int, colonne: int) -> Case | None:
        for cell in self.cells:
            if cell.ligne == ligne and cell.colonne == colonne:
                return cell
        return None

    def get_cell_from_pixel(self, x: int, y: int) -> Case | None:
        for cell in self.cells:
            if cell.rect.collidepoint(x, y):
                return cell
        return None

    def enregistrerCase(self, case: Case) -> None:
        if case not in self.casesImportantes:
            self.casesImportantes.append(case)

    def supprimerCaseSiVide(self, ligne: int, colonne: int) -> None:
        case = self.getCase(ligne, colonne)
        if case and not case.estImportante() and case in self.casesImportantes:
            self.casesImportantes.remove(case)

    def respecte_voisinage(self, cases_proposees: list[Case], bateau_actuel: Bateau) -> bool:
        for case in cases_proposees:
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    r, c = case.ligne + dr, case.colonne + dc
                    if self.estDansGrille(r, c):
                        voisine = self.getCase(r, c)
                        if voisine and voisine.bateau and voisine.bateau != bateau_actuel:
                            return False
        return True

    def calculer_cases_pour_bateau(self, b: Bateau, start_row: int, start_col: int, alignement: Alignement) -> list[Case] | None:
        cases: list[Case] = []
        for i in range(b.taille):
            row = start_row + (0 if alignement == Alignement.Horizontal else i)
            col = start_col + (i if alignement == Alignement.Horizontal else 0)
            if not self.estDansGrille(row, col):
                return None
            case = self.getCase(row, col)
            if case is None:
                return None
            if case.bateau is not None and case.bateau != b:
                return None
            cases.append(case)
        return cases

    def placementValide(self, b: Bateau, cases: list[Case] | None) -> bool:
        if cases is None or len(cases) != b.taille:
            return False
        return self.respecte_voisinage(cases, b)

    def placerBateau(self, b: Bateau, cases: list[Case]) -> None:
        if b not in self.bateaux:
            self.bateaux.append(b)

        for cell in self.cells:
            if cell.bateau == b:
                cell.retirerBateau()

        for c in cases:
            c.placerBateau(b)
            self.enregistrerCase(c)

        b.assignerCases(cases)
        b.row = cases[0].ligne
        b.column = cases[0].colonne

        anchor = cases[0]
        if b.alignement == Alignement.Horizontal:
            b.rect.midleft = anchor.rect.midleft
        else:
            b.rect.midtop = anchor.rect.midtop

    def tirer(self, cible: Case) -> ResultatTir:
        if cible is None:
            return ResultatTir.INVALIDE
        return cible.recevoirTir()

    def deplacementValide(self, b: Bateau, dir: DirectionDeplacement) -> bool:
        nouvelles = b.calculerCasesApresDeplacement(dir, self)
        if nouvelles is None or not self.placementValide(b, nouvelles):
            return False
        return True

    def mettreAJourCasesApresDeplacement(self, anciennes: list[Case], nouvelles: list[Case]) -> None:
        bateau = anciennes[0].bateau if anciennes else None
        for c in anciennes:
            c.retirerBateau()
        if bateau:
            self.placerBateau(bateau, nouvelles)

    def deplacerBateau(self, b: Bateau, dir: DirectionDeplacement) -> ResultatDeplacement:
        if b is None:
            return ResultatDeplacement.INVALIDE
        if any(c.is_clicked for c in b.getCasesOccupees()):
            return ResultatDeplacement.BLOQUE

        nouvelles = b.calculerCasesApresDeplacement(dir, self)
        if nouvelles is None or not self.placementValide(b, nouvelles):
            return ResultatDeplacement.INVALIDE

        anciennes = list(b.getCasesOccupees())
        self.mettreAJourCasesApresDeplacement(anciennes, nouvelles)
        return ResultatDeplacement.DEPLACE

    def aUnPorteAvionVivant(self) -> bool:
        return any(b.nom.startswith("Porte-avion") and not b.estCoule() for b in self.bateaux)

    def compterNaviresVivantsHorsPatrouilleurs(self) -> int:
        return sum(1 for b in self.bateaux if not b.nom.startswith("Patrouilleur") and not b.estCoule())

    def tousLesBateauxCoules(self) -> bool:
        return all(b.estCoule() for b in self.bateaux) if self.bateaux else False
