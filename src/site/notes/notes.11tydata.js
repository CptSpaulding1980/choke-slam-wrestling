name: Build and Deploy Digital Garden

on:
  push:
    branches: ["main"]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
      # Repo auschecken
      - name: Checkout repository
        uses: actions/checkout@v4

      # Node.js einrichten
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      # Dependencies installieren
      - name: Install dependencies
        run: npm install

      # Eleventy Build
      - name: Build Digital Garden site
        run: npm run build:eleventy

      # .nojekyll erzeugen (falls noch nicht vorhanden)
      - name: Create .nojekyll
        run: touch _site/.nojekyll

      # GitHub Pages konfigurieren
      - name: Setup Pages
        uses: actions/configure-pages@v5

      # Build-Artefakte hochladen (_site Ordner)
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: _site

      # Deployment auf GitHub Pages
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
