import Lean

open Lean

/-- Emit exactly one token-bound result for the gate. -/
def report (token status : String) (axioms : Array Name := #[]) : IO Unit :=
  IO.println <| "GATE_AUDIT " ++ (Json.mkObj [
    ("token", toJson token), ("status", toJson status),
    ("axioms", toJson (axioms.map Name.toString))]).compress

/-- Check is data only: never load its extensions or execute its initializers. -/
def main (args : List String) : IO UInt32 := do
  let [direction, token] := args | return 2
  unless direction == "proof" || direction == "disproof" do return 2
  initSearchPath (← findSysroot)
  let env ← importModules #[{ module := `Check }] {} (loadExts := false)
  let pinnedName := Name.str (Name.str Name.anonymous "Gate") "pinned"
  let some pinned := env.find? pinnedName | do
    report token "pin"
    return 1
  let conjecture := Expr.const (Name.str (Name.str Name.anonymous "Challenge") "Conjecture") []
  let expected := if direction == "proof" then conjecture else
    Expr.app (Expr.const (Name.str Name.anonymous "Not") []) conjecture
  unless Expr.equal pinned.type expected do
    report token "pin"
    return 1
  let axioms ← (collectAxioms pinnedName : CoreM (Array Name)).toIO'
    { fileName := "AuditMain", fileMap := default } { env := env }
  let allowed : Array Name := #[`propext, `Classical.choice, `Quot.sound]
  for ax in axioms do
    unless allowed.any (fun a => Name.beq a ax) do
      report token "axioms" axioms
      return 1
  report token "ok" axioms
  return 0
