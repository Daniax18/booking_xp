import { useState, useEffect } from 'react'
import { supabase } from '../../lib/supabase'
import { format } from 'date-fns'
import { fr } from 'date-fns/locale'
import { Calendar, User, Home } from 'lucide-react'

interface Booking {
  id: string
  check_in: string
  check_out: string
  guests: number
  total_price: number
  status: string
  special_requests: string | null
  created_at: string
  users: {
    full_name: string
    email: string
  }
  rooms: {
    name: string
    type: string
  }
}

const statusOptions = ['pending', 'confirmed', 'cancelled', 'completed']
const statusLabels: Record<string, string> = {
  pending: 'En attente',
  confirmed: 'Confirmée',
  cancelled: 'Annulée',
  completed: 'Terminée',
}

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  confirmed: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800',
  completed: 'bg-blue-100 text-blue-800',
}

export default function BookingManagement() {
  const [bookings, setBookings] = useState<Booking[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('all')

  useEffect(() => {
    loadBookings()
  }, [])

  const loadBookings = async () => {
    try {
      const { data, error } = await supabase
        .from('bookings')
        .select(`
          *,
          users (full_name, email),
          rooms (name, type)
        `)
        .order('created_at', { ascending: false })

      if (error) throw error
      setBookings(data || [])
    } catch (error) {
      console.error('Error loading bookings:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleStatusChange = async (bookingId: string, newStatus: string) => {
    try {
      const { error } = await supabase
        .from('bookings')
        .update({ status: newStatus })
        .eq('id', bookingId)

      if (error) throw error
      loadBookings()
    } catch (error) {
      console.error('Error updating booking:', error)
    }
  }

  const filteredBookings = filter === 'all'
    ? bookings
    : bookings.filter(b => b.status === filter)

  if (loading) {
    return <div className="text-center py-8">Chargement...</div>
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Gestion des Réservations</h2>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="input-field w-48"
        >
          <option value="all">Toutes</option>
          <option value="pending">En attente</option>
          <option value="confirmed">Confirmées</option>
          <option value="cancelled">Annulées</option>
          <option value="completed">Terminées</option>
        </select>
      </div>

      <div className="space-y-4">
        {filteredBookings.map((booking) => (
          <div key={booking.id} className="card hover:shadow-lg transition-shadow">
            <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-3">
                  <Home className="w-5 h-5 text-primary-600" />
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">{booking.rooms.name}</h3>
                    <p className="text-sm text-gray-600">{booking.rooms.type}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-3 mb-2">
                  <User className="w-4 h-4 text-gray-400" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">{booking.users.full_name}</p>
                    <p className="text-xs text-gray-500">{booking.users.email}</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-3 text-sm">
                  <div>
                    <p className="text-gray-500">Arrivée</p>
                    <p className="font-medium">{format(new Date(booking.check_in), 'dd MMM yyyy', { locale: fr })}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Départ</p>
                    <p className="font-medium">{format(new Date(booking.check_out), 'dd MMM yyyy', { locale: fr })}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Personnes</p>
                    <p className="font-medium">{booking.guests}</p>
                  </div>
                </div>

                {booking.special_requests && (
                  <div className="mt-3 bg-gray-50 rounded p-2">
                    <p className="text-xs text-gray-500">Demandes spéciales:</p>
                    <p className="text-sm text-gray-700">{booking.special_requests}</p>
                  </div>
                )}
              </div>

              <div className="lg:ml-6 mt-4 lg:mt-0 flex flex-col items-end space-y-3">
                <div className="text-right">
                  <p className="text-2xl font-bold text-primary-600">{booking.total_price}€</p>
                  <p className="text-xs text-gray-500">Prix total</p>
                </div>

                <select
                  value={booking.status}
                  onChange={(e) => handleStatusChange(booking.id, e.target.value)}
                  className={`px-3 py-2 rounded-lg text-sm font-medium ${statusColors[booking.status]} border-none cursor-pointer`}
                >
                  {statusOptions.map((status) => (
                    <option key={status} value={status}>
                      {statusLabels[status]}
                    </option>
                  ))}
                </select>

                <p className="text-xs text-gray-500">
                  Créée le {format(new Date(booking.created_at), 'dd MMM yyyy', { locale: fr })}
                </p>
              </div>
            </div>
          </div>
        ))}

        {filteredBookings.length === 0 && (
          <div className="card text-center py-12">
            <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">Aucune réservation trouvée</p>
          </div>
        )}
      </div>
    </div>
  )
}
