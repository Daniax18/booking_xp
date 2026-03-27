import { useState, FormEvent } from 'react'
import { supabase } from '../../lib/supabase'
import { useAuth } from '../../contexts/AuthContext'
import { X, Calendar, Users, CreditCard } from 'lucide-react'
import { differenceInDays } from 'date-fns'

interface Room {
  id: string
  name: string
  type: string
  capacity: number
  price_per_night: number
  description: string
}

interface BookingModalProps {
  room: Room
  onClose: () => void
}

export default function BookingModal({ room, onClose }: BookingModalProps) {
  const { user } = useAuth()
  const [checkIn, setCheckIn] = useState('')
  const [checkOut, setCheckOut] = useState('')
  const [guests, setGuests] = useState(1)
  const [specialRequests, setSpecialRequests] = useState('')
  const [paymentMethod, setPaymentMethod] = useState('carte')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const calculateTotal = () => {
    if (!checkIn || !checkOut) return 0
    const nights = differenceInDays(new Date(checkOut), new Date(checkIn))
    return nights > 0 ? nights * room.price_per_night : 0
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const totalPrice = calculateTotal()

      if (totalPrice <= 0) {
        throw new Error('Dates invalides')
      }

      const { data: booking, error: bookingError } = await supabase
        .from('bookings')
        .insert({
          user_id: user?.id,
          room_id: room.id,
          check_in: checkIn,
          check_out: checkOut,
          guests,
          total_price: totalPrice,
          status: 'pending',
          special_requests: specialRequests || null,
        })
        .select()
        .single()

      if (bookingError) throw bookingError

      const { error: paymentError } = await supabase
        .from('payments')
        .insert({
          booking_id: booking.id,
          amount: totalPrice,
          payment_method: paymentMethod,
          status: 'pending',
        })

      if (paymentError) throw paymentError

      setSuccess(true)
      setTimeout(() => {
        onClose()
        window.location.reload()
      }, 2000)
    } catch (err: any) {
      setError(err.message || 'Une erreur est survenue')
    } finally {
      setLoading(false)
    }
  }

  const today = new Date().toISOString().split('T')[0]
  const totalPrice = calculateTotal()
  const nights = checkIn && checkOut ? differenceInDays(new Date(checkOut), new Date(checkIn)) : 0

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">Réserver {room.name}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6">
          {success ? (
            <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-center">
              <p className="font-medium">Réservation créée avec succès!</p>
              <p className="text-sm mt-1">Redirection en cours...</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                  {error}
                </div>
              )}

              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-2">{room.type}</h3>
                <p className="text-sm text-gray-600 mb-3">{room.description}</p>
                <p className="text-lg font-bold text-primary-600">{room.price_per_night}€ / nuit</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="checkIn" className="block text-sm font-medium text-gray-700 mb-2">
                    <Calendar className="w-4 h-4 inline mr-2" />
                    Date d'arrivée
                  </label>
                  <input
                    id="checkIn"
                    type="date"
                    value={checkIn}
                    min={today}
                    onChange={(e) => setCheckIn(e.target.value)}
                    required
                    className="input-field"
                  />
                </div>
                <div>
                  <label htmlFor="checkOut" className="block text-sm font-medium text-gray-700 mb-2">
                    <Calendar className="w-4 h-4 inline mr-2" />
                    Date de départ
                  </label>
                  <input
                    id="checkOut"
                    type="date"
                    value={checkOut}
                    min={checkIn || today}
                    onChange={(e) => setCheckOut(e.target.value)}
                    required
                    className="input-field"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="guests" className="block text-sm font-medium text-gray-700 mb-2">
                  <Users className="w-4 h-4 inline mr-2" />
                  Nombre de personnes
                </label>
                <input
                  id="guests"
                  type="number"
                  value={guests}
                  min={1}
                  max={room.capacity}
                  onChange={(e) => setGuests(Number(e.target.value))}
                  required
                  className="input-field"
                />
                <p className="text-sm text-gray-500 mt-1">Capacité maximale: {room.capacity} personnes</p>
              </div>

              <div>
                <label htmlFor="paymentMethod" className="block text-sm font-medium text-gray-700 mb-2">
                  <CreditCard className="w-4 h-4 inline mr-2" />
                  Méthode de paiement
                </label>
                <select
                  id="paymentMethod"
                  value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                  className="input-field"
                >
                  <option value="carte">Carte bancaire</option>
                  <option value="paypal">PayPal</option>
                  <option value="virement">Virement bancaire</option>
                  <option value="especes">Espèces</option>
                </select>
              </div>

              <div>
                <label htmlFor="specialRequests" className="block text-sm font-medium text-gray-700 mb-2">
                  Demandes spéciales (optionnel)
                </label>
                <textarea
                  id="specialRequests"
                  value={specialRequests}
                  onChange={(e) => setSpecialRequests(e.target.value)}
                  rows={3}
                  className="input-field resize-none"
                  placeholder="Étage préféré, préférences alimentaires, etc."
                />
              </div>

              {nights > 0 && (
                <div className="bg-primary-50 border border-primary-200 rounded-lg p-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-gray-700">Prix par nuit:</span>
                    <span className="font-medium">{room.price_per_night}€</span>
                  </div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-gray-700">Nombre de nuits:</span>
                    <span className="font-medium">{nights}</span>
                  </div>
                  <div className="border-t border-primary-300 pt-2 mt-2 flex justify-between items-center">
                    <span className="text-lg font-bold text-gray-900">Total:</span>
                    <span className="text-2xl font-bold text-primary-600">{totalPrice}€</span>
                  </div>
                </div>
              )}

              <div className="flex space-x-3 pt-4">
                <button type="button" onClick={onClose} className="btn-secondary flex-1">
                  Annuler
                </button>
                <button type="submit" disabled={loading || !totalPrice} className="btn-primary flex-1">
                  {loading ? 'Réservation...' : `Confirmer (${totalPrice}€)`}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
