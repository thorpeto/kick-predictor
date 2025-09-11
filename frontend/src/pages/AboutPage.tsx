const AboutPage = () => {
  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-center mb-8">Über Kick Predictor</h1>
      
      <div className="card mb-8">
        <h2 className="text-bundesliga-red mb-4">Unser Projekt</h2>
        <p className="mb-4">
          Kick Predictor ist ein Projekt, das moderne Datenanalyse und maschinelles Lernen nutzt, um 
          präzise Vorhersagen für Bundesliga-Spiele zu treffen. Die Anwendung basiert auf historischen 
          Daten, aktuellen Formkurven und verschiedenen statistischen Faktoren.
        </p>
        <p>
          Ziel des Projekts ist es, Fußballfans und Interessierten einen datenbasierten Einblick in 
          kommende Spiele zu geben und die Wahrscheinlichkeiten verschiedener Ergebnisse zu visualisieren.
        </p>
      </div>
      
      <div className="card mb-8">
        <h2 className="text-bundesliga-red mb-4">Unser Vorhersagemodell</h2>
        <p className="mb-4">
          Das Herzstück von Kick Predictor ist unser Vorhersagemodell, das folgende Faktoren berücksichtigt:
        </p>
        <ul className="list-disc pl-6 mb-4 space-y-2">
          <li>Aktuelle Form der Teams (basierend auf den letzten 6 Spielen)</li>
          <li>Erzielte Tore und Gegentore</li>
          <li>Expected Goals (xG) als Maß für die Qualität der Torchancen</li>
          <li>Heimvorteil</li>
          <li>Historische Begegnungen zwischen den Teams</li>
        </ul>
        <p>
          Unser Modell wird kontinuierlich weiterentwickelt und mit neuen Daten trainiert, um die 
          Genauigkeit der Vorhersagen zu verbessern.
        </p>
      </div>
      
      <div className="card mb-8">
        <h2 className="text-bundesliga-red mb-4">Datenquellen</h2>
        <p className="mb-4">
          Die in Kick Predictor verwendeten Daten stammen aus verschiedenen öffentlichen Quellen, darunter:
        </p>
        <ul className="list-disc pl-6 space-y-2">
          <li>Offizielle Bundesliga-Statistiken</li>
          <li>Spezialisierte Fußball-Datenbanken</li>
          <li>Öffentliche Fußball-APIs</li>
        </ul>
      </div>
      
      <div className="card">
        <h2 className="text-bundesliga-red mb-4">Haftungsausschluss</h2>
        <p className="mb-4">
          Kick Predictor dient ausschließlich zu Informations- und Unterhaltungszwecken. Die Vorhersagen 
          basieren auf statistischen Modellen und sollten nicht als Grundlage für finanzielle Entscheidungen 
          verwendet werden.
        </p>
        <p>
          Fußballergebnisse unterliegen zahlreichen unvorhersehbaren Faktoren, und selbst die 
          ausgeklügeltsten Modelle können nicht alle Variablen berücksichtigen, die den Ausgang eines 
          Spiels beeinflussen können.
        </p>
      </div>
    </div>
  )
}

export default AboutPage
