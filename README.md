## n8n workflow: video_to_clip (sanitized)

Ce workflow prend des lignes d'une Google Sheet (les lignes avec État = "new"), télécharge la vidéo indiquée par l'URL, génère une transcription par l'api whisper, découpe la vidéo en segments notés par un LLM, affine/sélectionne les meilleurs clips, puis range les fichiers produits dans un dossier dédié au titre. Il met aussi à jour la feuille (date et statut) pour tracer l'avancement.

Résumé du flux:
- Lecture des lignes de la Google Sheet et filtrage sur État = "new".
- Pour chaque ligne:
	- Création du dossier clips/<titre_nettoyé>.
	- Téléchargement de la vidéo depuis la colonne URL.
	- Chaîne de traitements vidéo: transcribe → sliding_window → scoring → snappe_segments → refine → extract (et variantes).
	- Déplacement des clips générés dans clips/<titre>/valide.
	- Mise à jour de la Google Sheet (date de traitement, statut enProcess).

Note: Un second workflow (ex: `publish_clips`) peut ensuite publier les clips et marquer la ligne comme "published".

### Prérequis
- n8n installé et accessible.
- Accès Google et un credential n8n "Google Sheets OAuth2 API" configuré (à reconnecter après import).
- Une Google Sheet avec a minima les colonnes: URL, titre, description, sources, État, Date de traitement, chemin, hashtags (suivant votre usage).
- Un environnement Python contenant les scripts référencés sous `./src/` (download_video.py, transcribe.py, sliding_window.py, scoring.py, snappe_segments.py, refine.py, extract.py, etc.) et un Python exécutable sous `./bin/python` (ou adaptez les chemins dans les nodes Execute Command).
- Arborescence de dossiers attendue: `./clips/` et `./src/output/` (créées si besoin).

### Mise en place (import et configuration)
1. Importer le fichier `video_to_clip.sanitized.json` dans n8n.
2. Ouvrir les nodes Google Sheets et:
	 - Reconnecter l'credential "Google Sheets OAuth2 API".
	 - Renseigner le Spreadsheet ID et la feuille (gid/nom) de votre document.
3. Vérifier/adapter les chemins des nodes Execute Command pour qu'ils pointent bien vers votre environnement (les chemins utilisent `$HOME`).
4. Vérifier que les scripts Python existent et sont exécutables.
5. S'assurer que la Google Sheet contient des lignes avec `État = new` et des valeurs cohérentes pour `URL`, `titre`, `description`, `sources`, `hashtags`, `chemin` selon vos besoins.

### Exécution
- Dans n8n, ouvrir le workflow et cliquer sur "Execute workflow".
- Le workflow va:
	- Lire les lignes à traiter dans la Google Sheet.
	- Lancer la chaîne de traitement vidéo et générer les clips.
	- Mettre à jour la feuille (date, statut enProcess) et ranger les fichiers dans `clips/<titre>/valide`.

### Contenu nettoyé (sanitized)
Ce dossier contient une exportation nettoyée pour un partage public sans fuite d'infos sensibles.

Supprimé/masqué:
- ID et URL directs de la Google Sheet.
- Références aux credentials (à reconfigurer après import dans n8n).
- Identifiants de l'instance n8n (meta.instanceId, versionId, workflow id).
- Chemins absolus incluant votre nom d'utilisateur; remplacés par `$HOME`.

Après import, à reconfigurer:
- Dans les nodes Google Sheets: Spreadsheet ID et feuille (gid/nom).
- Reconnexion du credential "Google Sheets OAuth2 API".
- Vérification des chemins/structures du projet sous `./...`.

Astuce: vous pouvez remplacer `$HOME` par une autre variable d'environnement (par ex. `$PROJECT_HOME`).
