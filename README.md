# Flient Smart Lock - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Bedien je Flient smart locks via Home Assistant. Ondersteunt openen, sluiten en batterijstatus.

## Vereisten

- Een Flient account met gekoppelde sloten
- Een Flient Hub gekoppeld aan je slot — nodig voor bediening op afstand
- Home Assistant 2024.1.0 of nieuwer

## Installatie via HACS

1. Open HACS in Home Assistant
2. Klik op **Integraties** → **⋮** → **Aangepaste repository's**
3. Voeg toe: `https://github.com/Flient-smart-Lock/ha-flient` (categorie: Integratie)
4. Zoek naar **Flient Smart Lock** en klik **Downloaden**
5. Herstart Home Assistant

## Configuratie

1. Ga naar **Instellingen** → **Apparaten en services** → **Integratie toevoegen**
2. Zoek naar **Flient**
3. Log in met je Flient e-mailadres en wachtwoord
4. Je sloten verschijnen automatisch

## Functies

- 🔒 **Slot vergrendelen/ontgrendelen** — via Flient Hub (cloud)
- 🔋 **Batterijstatus** — percentage per slot
- 🔄 **Automatische updates** — status wordt elke 30 seconden bijgewerkt

## Beperkingen

- Bediening werkt alleen via de Flient Hub — directe Bluetooth wordt niet ondersteund
- Fysieke opens en auto-lock worden niet altijd direct gerapporteerd

## Support

Vragen? Neem contact op via [info@flient.nl](mailto:info@flient.nl) of bezoek [flient.net](https://flient.net).
