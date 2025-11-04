ugbib_modell
============

Implementiert bibModell zur Darstellung von Daten in PostgreSQL.

In gewisser Weise ist bibModell eine Leichtgewicht-Variante von Paketen wie SQLAlchemy. Ich habe es für meine eigenen Bedürfnisse entwickelt. Insb. trägt bibModell meinem Ansatz Rechnung, dass die gesamte Benutzerverwaltung auf der Ebene von PostgreSQL erledigt wird. D.h. insb., dass...

* ... die Authentifizierung der Benutzer gegen die PostgreSQL-Datenbank gecheckt wird
* ... dass der Benutzer sich in der GUI anmelden muss und seinen eigenen Datenbank-Connector bekommt.

Beides ist ungewöhnlich, erschien mir aber für die Architektur meiner Anwendungen sinnvoll.

Dazu gehören insb. die Klassen

* Feld
* Modell
* Relation

Das Paket ist kaum direkt verwendbar, bei Interesse kann man sich aber gerne an mich wenden (ulrich@fam-goebel.de).
