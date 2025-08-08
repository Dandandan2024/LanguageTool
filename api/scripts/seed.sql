-- Minimal seed: two Spanish cloze cards
INSERT INTO cards(language, type, payload)
VALUES
('es','cloze','{"text":"El ___ duerme en la silla.","answer":"gato","hints":["animal doméstico"]}'),
('es','cloze','{"text":"Mi ___ bebe leche.","answer":"gato","hints":["animal doméstico"]}');
