import { useCurrentTable } from '../services/api'

interface Team {
  id: number;
  name: string;
  short_name: string;
  logo_url?: string;
}

interface TableEntry {
  position: number;
  team: Team;
  matches_played: number;
  wins: number;
  draws: number;
  losses: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  points: number;
}

const TablePage = () => {
  const { data: tableData, loading, error } = useCurrentTable()

  // Funktion zur Bestimmung der Tabellenfarben basierend auf der Position
  const getPositionColor = (position: number): string => {
    if (position <= 4) {
      return 'bg-green-100 text-green-800' // Champions League
    } else if (position <= 6) {
      return 'bg-blue-100 text-blue-800' // Europa League
    } else if (position <= 7) {
      return 'bg-purple-100 text-purple-800' // Conference League
    } else if (position >= 16) {
      return 'bg-red-100 text-red-800' // Abstieg
    } else {
      return 'bg-gray-50' // Mittfeld
    }
  }

  // Responsive Spalten für mobile vs desktop
  const TableHeader = () => (
    <thead className="bg-bundesliga-navy text-white">
      <tr>
        <th className="px-2 py-3 text-left text-xs font-medium uppercase tracking-wider">Pos</th>
        <th className="px-3 py-3 text-left text-xs font-medium uppercase tracking-wider">Team</th>
        <th className="px-2 py-3 text-center text-xs font-medium uppercase tracking-wider hidden sm:table-cell">Sp</th>
        <th className="px-2 py-3 text-center text-xs font-medium uppercase tracking-wider hidden md:table-cell">S</th>
        <th className="px-2 py-3 text-center text-xs font-medium uppercase tracking-wider hidden md:table-cell">U</th>
        <th className="px-2 py-3 text-center text-xs font-medium uppercase tracking-wider hidden md:table-cell">N</th>
        <th className="px-2 py-3 text-center text-xs font-medium uppercase tracking-wider hidden sm:table-cell">Tore</th>
        <th className="px-2 py-3 text-center text-xs font-medium uppercase tracking-wider hidden sm:table-cell">Diff</th>
        <th className="px-3 py-3 text-center text-xs font-medium uppercase tracking-wider">Pkt</th>
      </tr>
    </thead>
  )

  const TableRow = ({ entry }: { entry: TableEntry }) => (
    <tr className={`${getPositionColor(entry.position)} border-b hover:bg-gray-50`}>
      <td className="px-2 py-4 whitespace-nowrap text-sm font-medium">
        {entry.position}
      </td>
      <td className="px-3 py-4 whitespace-nowrap">
        <div className="flex items-center">
          {entry.team.logo_url && (
            <img 
              className="h-6 w-6 mr-2 rounded" 
              src={entry.team.logo_url} 
              alt={entry.team.short_name}
              onError={(e) => {
                e.currentTarget.style.display = 'none'
              }}
            />
          )}
          <div>
            <div className="text-sm font-medium text-gray-900 hidden sm:block">
              {entry.team.name}
            </div>
            <div className="text-sm font-medium text-gray-900 sm:hidden">
              {entry.team.short_name}
            </div>
          </div>
        </div>
      </td>
      <td className="px-2 py-4 whitespace-nowrap text-sm text-gray-900 text-center hidden sm:table-cell">
        {entry.matches_played}
      </td>
      <td className="px-2 py-4 whitespace-nowrap text-sm text-gray-900 text-center hidden md:table-cell">
        {entry.wins}
      </td>
      <td className="px-2 py-4 whitespace-nowrap text-sm text-gray-900 text-center hidden md:table-cell">
        {entry.draws}
      </td>
      <td className="px-2 py-4 whitespace-nowrap text-sm text-gray-900 text-center hidden md:table-cell">
        {entry.losses}
      </td>
      <td className="px-2 py-4 whitespace-nowrap text-sm text-gray-900 text-center hidden sm:table-cell">
        {entry.goals_for}:{entry.goals_against}
      </td>
      <td className="px-2 py-4 whitespace-nowrap text-sm text-gray-900 text-center hidden sm:table-cell">
        {entry.goal_difference > 0 ? '+' : ''}{entry.goal_difference}
      </td>
      <td className="px-3 py-4 whitespace-nowrap text-sm font-bold text-gray-900 text-center">
        {entry.points}
      </td>
    </tr>
  )

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-center mb-8">Aktuelle Tabelle</h1>
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-bundesliga-red"></div>
          <p className="mt-4">Lade Tabellendaten...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-center mb-8">Aktuelle Tabelle</h1>
        <div className="text-center text-red-600">
          <p>{error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="mt-4 bg-bundesliga-red text-white px-4 py-2 rounded hover:bg-red-700"
          >
            Erneut versuchen
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-center mb-8">1. Bundesliga - Saison 2025/26</h1>
      
      {/* Legende */}
      <div className="mb-6 grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
        <div className="flex items-center">
          <div className="w-4 h-4 bg-green-100 border border-green-300 mr-2"></div>
          <span>Champions League (1-4)</span>
        </div>
        <div className="flex items-center">
          <div className="w-4 h-4 bg-blue-100 border border-blue-300 mr-2"></div>
          <span>Europa League (5-6)</span>
        </div>
        <div className="flex items-center">
          <div className="w-4 h-4 bg-purple-100 border border-purple-300 mr-2"></div>
          <span>Conference League (7)</span>
        </div>
        <div className="flex items-center">
          <div className="w-4 h-4 bg-red-100 border border-red-300 mr-2"></div>
          <span>Abstieg (16-18)</span>
        </div>
      </div>

      {/* Tabelle */}
      <div className="bg-white shadow-lg rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <TableHeader />
            <tbody className="bg-white divide-y divide-gray-200">
              {tableData && tableData.map((entry) => (
                <TableRow key={entry.team.id} entry={entry} />
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Mobile Hinweis */}
      <div className="mt-4 text-xs text-gray-500 sm:hidden">
        Tippe auf ein Team für mehr Details. Für alle Spalten verwende ein größeres Display.
      </div>

      {/* Zusätzliche Informationen */}
      <div className="mt-8 bg-gray-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">Tabellenstand</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <strong>Spiele gespielt:</strong> {tableData?.[0]?.matches_played || 0} von 34
          </div>
          <div>
            <strong>Stand:</strong> {new Date().toLocaleDateString('de-DE')}
          </div>
          <div>
            <strong>Nächster Spieltag:</strong> {(tableData?.[0]?.matches_played || 0) + 1}
          </div>
        </div>
      </div>
    </div>
  )
}

export default TablePage