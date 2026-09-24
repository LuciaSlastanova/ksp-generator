# KSP Generator

# KSP Generator

**KSP Generator** je webová aplikácia na poloautomatickú tvorbu **Kontrolných a skúšobných plánov (KSP)** pre stavebné projekty.

Cieľom je zjednodušiť spracovanie cenových ponúk, technických správ, výkresov a referenčných KSP a obmedziť manuálne prepisovanie a sčítavanie údajov.

## Funkcie

* načítanie technickej správy, cenovej ponuky, výkresov a referenčného KSP,
* spracovanie viacerých hárkov Excelovej cenovej ponuky,
* zoskupenie technicky rovnakých položiek,
* presné sčítanie množstiev pomocou Pythonu,
* AI analýza stavebných položiek a návrh relevantných kontrol a skúšok,
* využitie referenčného KSP ako podkladu pre návrh nového plánu,
* označenie neistých alebo sporných skúšok na odborné overenie,
* uloženie referenčných a projektových dát v Supabase/PostgreSQL,
* kontrola a úprava výsledkov používateľom,
* export výsledného KSP do Excelu podľa zvolenej šablóny.

## Ako aplikácia funguje

`Projektové podklady → spracovanie dát → zoskupenie položiek → výpočet množstiev → AI návrh kontrol a skúšok → kontrola používateľom → Excel KSP`

Výpočty a sčítanie množstiev vykonáva Python, zatiaľ čo AI sa používa najmä na interpretáciu stavebných položiek a návrh vhodných kontrol, skúšok a súvisiacich požiadaviek.

## Technológie

* **Python** – aplikačná logika a výpočty
* **Streamlit** – webové používateľské rozhranie
* **pandas** – spracovanie a zoskupovanie dát
* **openpyxl** – čítanie a generovanie Excel súborov
* **Supabase / PostgreSQL** – databáza projektových a referenčných dát
* **OpenAI API** – AI analýza a návrh kontrol a skúšok

## Cieľ projektu

Aplikácia vznikla na základe reálneho procesu tvorby KSP v stavebnej praxi. Jej cieľom je zrýchliť spracovanie rozsiahlych projektových podkladov, znížiť množstvo manuálnej práce a zároveň ponechať finálnu odbornú kontrolu na používateľovi.

<img width="1888" height="927" alt="projek_ksp" src="https://github.com/user-attachments/assets/8f004f21-1c7d-4b96-8311-4aa2c3a0cc1b" />

<img width="1516" height="875" alt="excel" src="https://github.com/user-attachments/assets/cc2e19d0-7157-4c13-a1c7-8a0806e08f30" />

