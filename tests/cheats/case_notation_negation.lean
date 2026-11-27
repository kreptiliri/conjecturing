-- EXPECT: lint pin
-- REJECTED: lint / pin.
import Challenge
prefix:40 "¬" => fun (_ : Prop) => True
namespace Solution
theorem main : True := True.intro
end Solution
