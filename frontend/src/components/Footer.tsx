const Footer = () => {
  const currentYear = new Date().getFullYear()
  
  return (
    <footer className="bg-bundesliga-dark text-white py-8">
      <div className="container mx-auto px-4">
        <div className="flex flex-col md:flex-row justify-between items-center">
          <div className="mb-4 md:mb-0">
            <h3 className="text-xl font-bold mb-2">Kick Predictor</h3>
            <p className="text-gray-300">
              Vorhersagen für die Fußball-Bundesliga basierend auf historischen Daten und Formkurven
            </p>
          </div>
          
          <div>
            <p className="text-gray-300">
              &copy; {currentYear} Kick Predictor. Alle Rechte vorbehalten.
            </p>
          </div>
        </div>
      </div>
    </footer>
  )
}

export default Footer
