class_name Tourist
extends Protester
## A tourist during a tourist rush: walks to a sight, stands there waving and taking photos, then goes home.

const SAYS := ["dz_tourist_say1", "dz_tourist_say2", "dz_tourist_say3", "dz_tourist_say4"]


func start(from: Vector2, at: Vector2, look: Vector2, why: String) -> void:
	super.start(from, at, look, why)
	if placard:
		placard.queue_free()
		placard = null


func _shout() -> void:
	if life and life.city:
		life.speech(self, Loc.t(SAYS.pick_random()), 2.4)
