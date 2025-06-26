# Plan de Refactoring - Chatbot Raphaël PICARD

## 📋 Analyse du code actuel

### Problèmes identifiés :

- **Responsabilités mélangées** : lecture de fichiers, logique métier, interface UI dans un seul fichier
- **Code dupliqué** : création de messages répétée
- **Configuration hardcodée** : clés API, chemins de fichiers
- **Pas de gestion d'erreurs** centralisée
- **Types inconsistants** : mélange de `str | None` et `str`
- **Logique de retry basique** : pas de limite de tentatives

## 🎯 Architecture cible

### Structure des dossiers :

```
raph/
├── config/
│   ├── __init__.py
│   ├── settings.py          # Configuration centralisée
│   └── prompts.py           # Templates de prompts
├── core/
│   ├── __init__.py
│   ├── models.py            # Classes Pydantic (Evaluation, etc.)
│   ├── profile_loader.py    # Chargement des données de profil
│   └── message_formatter.py # Formatage des messages
├── services/
│   ├── __init__.py
│   ├── chat_service.py      # Service de chat principal
│   ├── evaluation_service.py # Service d'évaluation
│   └── retry_service.py     # Logique de retry
├── api/
│   ├── __init__.py
│   ├── openai_client.py     # Client OpenAI configuré
│   └── gemini_client.py     # Client Gemini configuré
├── ui/
│   ├── __init__.py
│   └── gradio_interface.py  # Interface Gradio
├── utils/
│   ├── __init__.py
│   ├── file_utils.py        # Utilitaires de fichiers
│   └── logger.py            # Configuration des logs
├── main.py                  # Point d'entrée principal
├── requirements.txt         # Dépendances
└── REFACTORING_PLAN.md     # Ce fichier
```

## 📝 Tâches de refactoring

### Phase 1 : Configuration et utilitaires

- [x] **1.1** ✅ Créer `config/settings.py` pour centraliser la configuration - INTÉGRÉ
- [x] **1.2** ✅ Créer `config/prompts.py` pour les templates de prompts - INTÉGRÉ
- [x] **1.3** ✅ Créer `utils/file_utils.py` pour la lecture de fichiers - INTÉGRÉ
- [x] **1.4** ✅ Créer `utils/logger.py` pour la gestion des logs - INTÉGRÉ

### Phase 2 : Modèles et clients API

- [x] **2.1** ✅ Créer `core/models.py` avec les classes Pydantic - INTÉGRÉ
- [x] **2.2** ✅ Créer `api/openai_client.py` avec client configuré - INTÉGRÉ
- [x] **2.3** ✅ Créer `api/gemini_client.py` avec client configuré - INTÉGRÉ
- [x] **2.4** ✅ Créer `core/message_formatter.py` pour le formatage des messages - INTÉGRÉ

### Phase 3 : Services métier

- [x] **3.1** ✅ Créer `core/profile_loader.py` pour charger les données du profil - INTÉGRÉ
- [x] **3.2** ✅ Créer `services/chat_service.py` pour la logique de chat - INTÉGRÉ
- [x] **3.3** Créer `services/evaluation_service.py` pour l'évaluation
- [x] **3.4** Créer `services/retry_service.py` pour la logique de retry avancée

### Phase 4 : Interface et point d'entrée

- [x] **4.1** Créer `ui/gradio_interface.py` pour l'interface utilisateur
- [x] **4.2** Refactorer `me.py` comme point d'entrée simple
- [x] **4.3** Créer `requirements.txt`

### Phase 5 : Améliorations

- [x] **5.1** Ajouter gestion d'erreurs robuste
- [x] **5.2** Ajouter limite de tentatives de retry
- [x] **5.3** Ajouter métriques et monitoring
- [x] **5.4** Ajouter tests unitaires (optionnel)

## 🚀 Fonctionnalités améliorées

### Gestion des erreurs :

- Try/catch appropriés dans chaque service
- Messages d'erreur utilisateur-friendly
- Fallback en cas d'échec des services externes

### Configuration flexible :

- Variables d'environnement pour tous les paramètres
- Configuration par fichier YAML/JSON (optionnel)
- Validation de la configuration au démarrage

### Retry intelligent :

- Limite du nombre de tentatives
- Délai progressif entre les tentatives
- Métriques de qualité

### Logging :

- Logs structurés avec niveaux appropriés
- Rotation des fichiers de logs
- Monitoring des performances

## 📊 Bénéfices attendus

1. **Maintenabilité** : Code organisé par responsabilité
2. **Testabilité** : Services isolés et injectables
3. **Évolutivité** : Ajout facile de nouvelles fonctionnalités
4. **Configuration** : Paramètres centralisés et flexibles
5. **Robustesse** : Gestion d'erreurs et retry appropriés
6. **Monitoring** : Logs et métriques pour le debugging

## ⚡ Migration

La migration se fera de manière incrémentale :

- **Une tâche à la fois** : Chaque tâche doit être validée avant de passer à la suivante
- **Test de régression** : À chaque tâche, validation que les tâches précédentes fonctionnent toujours
- **Confirmation explicite** : Demander confirmation avant de passer à la tâche suivante
- L'interface utilisateur reste fonctionnelle pendant la migration
- Possibilité de rollback à chaque étape

## 📋 Statut des tâches

### Phase 1 : Configuration et utilitaires

- [x] **1.1** ✅ Créer `config/settings.py` pour centraliser la configuration - INTÉGRÉ
- [x] **1.2** ✅ Créer `config/prompts.py` pour les templates de prompts - INTÉGRÉ
- [x] **1.3** ✅ Créer `utils/file_utils.py` pour la lecture de fichiers - INTÉGRÉ
- [x] **1.4** ✅ Créer `utils/logger.py` pour la gestion des logs - INTÉGRÉ

### Phase 2 : Modèles et clients API

- [x] **2.1** ✅ Créer `core/models.py` avec les classes Pydantic - INTÉGRÉ
- [x] **2.2** ✅ Créer `api/openai_client.py` avec client configuré - INTÉGRÉ
- [x] **2.3** ✅ Créer `api/gemini_client.py` avec client configuré - INTÉGRÉ
- [x] **2.4** ✅ Créer `core/message_formatter.py` pour le formatage des messages - INTÉGRÉ

### Phase 3 : Services métier

- [x] **3.1** ✅ Créer `core/profile_loader.py` pour charger les données du profil - INTÉGRÉ
- [x] **3.2** ✅ Créer `services/chat_service.py` pour la logique de chat - INTÉGRÉ
- [x] **3.3** ✅ Créer `services/evaluation_service.py` pour l'évaluation - INTÉGRÉ
- [x] **3.4** ✅ Créer `services/retry_service.py` pour la logique de retry avancée - INTÉGRÉ

### Phase 4 : Interface et point d'entrée

- [x] **4.1** Créer `ui/gradio_interface.py` pour l'interface utilisateur
- [x] **4.2** Refactorer `me.py` comme point d'entrée simple
- [x] **4.3** Créer `requirements.txt`

### Phase 5 : Améliorations

- [x] **5.1** Ajouter gestion d'erreurs robuste
- [x] **5.2** Ajouter limite de tentatives de retry
- [x] **5.3** Ajouter métriques et monitoring
