import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { supabase } from '../lib/supabase'
import { Calendar, LogOut, User, Home } from 'lucide-react'
import RoomList from '../components/client/RoomList'
import BookingList from '../components/client/BookingList'
import BookingModal from '../components/client/BookingModal'

type TabType = 'rooms' | 'bookings' | 'profile'

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

export default function ClientDashboard() {
  const { profile, signOut } = useAuth()
  const [activeTab, setActiveTab] = useState<TabType>('rooms')
  const [rooms, setRooms] = useState<Room[]>([])
  const [selectedRoom, setSelectedRoom] = useState<Room | null>(null)
  const [showBookingModal, setShowBookingModal] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadRooms()
  }, [])

  const loadRooms = async () => {
    try {
      const { data, error } = await supabase
        .from('rooms')
        .select('*')
        .eq('status', 'available')
        .order('created_at', { ascending: false })

      if (error) throw error
      setRooms(data || [])
    } catch (error) {
      console.error('Error loading rooms:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleBookRoom = (room: Room) => {
    setSelectedRoom(room)
    setShowBookingModal(true)
  }

  const handleSignOut = async () => {
    await signOut()
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
                <Home className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-xl font-bold text-gray-900">Gestion Réservation</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">Bienvenue, {profile?.full_name}</span>
              <button onClick={handleSignOut} className="btn-secondary flex items-center space-x-2">
                <LogOut className="w-4 h-4" />
                <span>Déconnexion</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8">
              <button
                onClick={() => setActiveTab('rooms')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'rooms'
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Home className="w-5 h-5" />
                  <span>Chambres disponibles</span>
                </div>
              </button>
              <button
                onClick={() => setActiveTab('bookings')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'bookings'
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Calendar className="w-5 h-5" />
                  <span>Mes réservations</span>
                </div>
              </button>
              <button
                onClick={() => setActiveTab('profile')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'profile'
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <User className="w-5 h-5" />
                  <span>Mon profil</span>
                </div>
              </button>
            </nav>
          </div>
        </div>

        <div className="mt-6">
          {activeTab === 'rooms' && (
            <RoomList rooms={rooms} loading={loading} onBookRoom={handleBookRoom} />
          )}
          {activeTab === 'bookings' && <BookingList />}
          {activeTab === 'profile' && (
            <div className="card max-w-2xl">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Mon Profil</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Nom complet</label>
                  <input type="text" value={profile?.full_name || ''} disabled className="input-field bg-gray-50" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                  <input type="email" value={profile?.email || ''} disabled className="input-field bg-gray-50" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Role</label>
                  <input type="text" value={profile?.role || ''} disabled className="input-field bg-gray-50" />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {showBookingModal && selectedRoom && (
        <BookingModal
          room={selectedRoom}
          onClose={() => {
            setShowBookingModal(false)
            setSelectedRoom(null)
          }}
        />
      )}
    </div>
  )
}
