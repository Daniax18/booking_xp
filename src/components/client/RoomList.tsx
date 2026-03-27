import { Users, Wifi, Tv, Coffee, CheckCircle } from 'lucide-react'

interface Room {
  id: string
  name: string
  type: string
  capacity: number
  price_per_night: number
  description: string
  amenities: string[]
  image_url: string
  status: string
}

interface RoomListProps {
  rooms: Room[]
  loading: boolean
  onBookRoom: (room: Room) => void
}

const amenityIcons: Record<string, any> = {
  wifi: Wifi,
  tv: Tv,
  breakfast: Coffee,
}

export default function RoomList({ rooms, loading, onBookRoom }: RoomListProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="card animate-pulse">
            <div className="bg-gray-200 h-48 rounded-lg mb-4"></div>
            <div className="h-4 bg-gray-200 rounded mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-2/3"></div>
          </div>
        ))}
      </div>
    )
  }

  if (rooms.length === 0) {
    return (
      <div className="card text-center py-12">
        <p className="text-gray-600">Aucune chambre disponible pour le moment</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {rooms.map((room) => (
        <div key={room.id} className="card hover:shadow-lg transition-shadow">
          <div className="relative h-48 mb-4 rounded-lg overflow-hidden bg-gradient-to-br from-primary-100 to-primary-200">
            {room.image_url ? (
              <img src={room.image_url} alt={room.name} className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <span className="text-6xl text-primary-600">{room.name[0]}</span>
              </div>
            )}
            <div className="absolute top-3 right-3 bg-white px-3 py-1 rounded-full text-sm font-medium text-primary-600">
              {room.type}
            </div>
          </div>

          <h3 className="text-xl font-bold text-gray-900 mb-2">{room.name}</h3>
          <p className="text-gray-600 text-sm mb-4 line-clamp-2">{room.description}</p>

          <div className="flex items-center space-x-2 text-gray-600 mb-4">
            <Users className="w-4 h-4" />
            <span className="text-sm">{room.capacity} personnes</span>
          </div>

          {room.amenities && room.amenities.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-4">
              {room.amenities.map((amenity, index) => {
                const Icon = amenityIcons[amenity.toLowerCase()] || CheckCircle
                return (
                  <div key={index} className="flex items-center space-x-1 bg-gray-100 px-2 py-1 rounded-md text-xs text-gray-700">
                    <Icon className="w-3 h-3" />
                    <span>{amenity}</span>
                  </div>
                )
              })}
            </div>
          )}

          <div className="flex items-center justify-between pt-4 border-t border-gray-200">
            <div>
              <span className="text-2xl font-bold text-primary-600">{room.price_per_night}€</span>
              <span className="text-gray-600 text-sm"> / nuit</span>
            </div>
            <button onClick={() => onBookRoom(room)} className="btn-primary">
              Réserver
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}
