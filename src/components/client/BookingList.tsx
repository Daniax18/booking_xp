import { useState, useEffect } from 'react'
import { supabase } from '../../lib/supabase'
import { useAuth } from '../../contexts/AuthContext'
import { Calendar, Users, CreditCard } from 'lucide-react'
import { format } from 'date-fns'
import { fr } from 'date-fns/locale'

interface Booking {
  id: string
  check_in: string
  check_out: string
  guests: number
  total_price: number
  status: string
  special_requests: string | null
  created_at: string
  rooms: {
    name: string
    type: string
  }
  payments: {
    status: string
    payment_method: string
  }[]
}

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  confirmed: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800',
  completed: 'bg-blue-100 text-blue-800',
}

const statusLabels: Record<string, string> = {
  pending: 'En attente',
  confirmed: 'Confirmée',
  cancelled: 'Annulée',
  completed: 'Terminée',
}

export default function BookingList() {
  const { user } = useAuth()
  const [bookings, setBookings] = useState<Booking[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadBookings()
  }, [])

  const loadBookings = async () => {
    try {
      const { data, error } = await supabase
        .from('bookings')
        .select(`
          *,
          rooms (name, type),
          payments (status, payment_method)
        `)
        .eq('user_id', user?.id || '')
        .order('created_at', { ascending: false })

      if (error) throw error
      setBookings(data || [])
    } catch (error) {
      console.error('Error loading bookings:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="card animate-pulse">
            <div className="h-6 bg-gray-200 rounded mb-4 w-1/3"></div>
            <div className="h-4 bg-gray-200 rounded mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-2/3"></div>
          </div>
        ))}
      </div>
    )
  }

  if (bookings.length === 0) {
    return (
      <div className="card text-center py-12">
        <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600">Vous n'avez aucune réservation pour le moment</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {bookings.map((booking) => (
        <div key={booking.id} className="card hover:shadow-lg transition-shadow">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-4">
            <div>
              <h3 className="text-xl font-bold text-gray-900">{booking.rooms.name}</h3>
              <p className="text-gray-600 text-sm">{booking.rooms.type}</p>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusColors[booking.status]} mt-2 md:mt-0 inline-block`}>
              {statusLabels[booking.status]}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div className="flex items-center space-x-3 text-gray-700">
              <Calendar className="w-5 h-5 text-primary-600" />
              <div>
                <p className="text-sm font-medium">Arrivée</p>
                <p className="text-sm">{format(new Date(booking.check_in), 'dd MMMM yyyy', { locale: fr })}</p>
              </div>
            </div>
            <div className="flex items-center space-x-3 text-gray-700">
              <Calendar className="w-5 h-5 text-primary-600" />
              <div>
                <p className="text-sm font-medium">Départ</p>
                <p className="text-sm">{format(new Date(booking.check_out), 'dd MMMM yyyy', { locale: fr })}</p>
              </div>
            </div>
            <div className="flex items-center space-x-3 text-gray-700">
              <Users className="w-5 h-5 text-primary-600" />
              <div>
                <p className="text-sm font-medium">Personnes</p>
                <p className="text-sm">{booking.guests}</p>
              </div>
            </div>
            <div className="flex items-center space-x-3 text-gray-700">
              <CreditCard className="w-5 h-5 text-primary-600" />
              <div>
                <p className="text-sm font-medium">Prix total</p>
                <p className="text-sm font-bold">{booking.total_price}€</p>
              </div>
            </div>
          </div>

          {booking.special_requests && (
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-sm font-medium text-gray-700 mb-1">Demandes spéciales</p>
              <p className="text-sm text-gray-600">{booking.special_requests}</p>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
