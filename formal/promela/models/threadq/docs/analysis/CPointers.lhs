\section{Pointer Simplification}

This includes Haskell code implementing this.
\begin{code}
module CPointers where

import Data.Map (Map)
import qualified Data.Map as M
\end{code}

\subsubsection{Values}

We need to distinguish three kinds of objects: scalars, pointers and structs.
The value of a pointer is a RAM address.
A struct is an ordered list of named objects, and its value is the list of values
of those objects.
\begin{code}
type Number = Int
type Address = Int
type FieldName = String
type Field = (FieldName,Value)
type FieldList = [Field]
data Value
  = Scalar  Number
  | Pointer Address
  | Struct  FieldList -- Fields must be unique
\end{code}

\subsubsection{Located Objects}

All three can either be in RAM, or internal CPU registers.
An object in RAM has an associated address.
\begin{code}
data Location = Internal | RAM Address
type Object = (Location, Value)
addrOf :: Monad m => Object -> m Address
addrOf (RAM addr,_)  =  return addr
addrOf _             =  fail "Internal objects have no address"
\end{code}

\subsubsection{Sizing and Offsets}

For field address calculations,
we assume that scalars and pointers have size one.
\begin{code}
type Size = Int
sizeOf :: Value -> Size
sizeOf (Struct fs)  =  sum $ map (sizeOf . snd) fs
sizeOf _            =  1
\end{code}

\newpage
Given a struct field, we are not just interested in its value,
but its location relative to that of the struct as a whole:
\begin{code}
type Offset = Int
getField :: Monad m => FieldName -> FieldList -> m (Offset,Value)
getField f fs = getF f 0 fs
getF f _ [] = error ("getField: no such field '"++f++"'")
getF f offset ((fld,val):rest)
  | f == fld   =  return (offset,val)
  | otherwise  =  getF f (offset + sizeOf val) rest
\end{code}

\subsubsection{Single-Field Structs}

Some structs have a single field
(usually as an artefact of how conditional compilation is used).
It is useful to be able test for this:
\begin{code}
hasUniqueField :: FieldList -> Bool
hasUniqueField [_]  =  True
hasUniqueField  _   =  False
theUniqueField :: Monad m => FieldList -> m Field
theUniqueField [f]  =  return f
theUniqueField _    =  fail "theUniqueField: no unique field"
\end{code}

\subsubsection{C Pointer Syntax}

\begin{eqnarray*}
   s &:& \mbox{A variable holding some \texttt{struct}}
\\ f &:& \mbox{A field within that \texttt{struct}}
\\ p &:& \mbox{A pointer to that \texttt{struct}}
\\ q &:& \mbox{A pointer-valued field within that \texttt{struct}}
\\ \& &:& \mbox{returns address of its argument}
\\ *  &:& \mbox{pointer dereference}
\end{eqnarray*}
\begin{code}
data ValExpr
  = Var String             -- s
  | DeRef PtrExpr          -- *p
  | VField ValExpr String  -- s.f
data PtrExpr
  = Ptr String             -- p
  | AddrOf ValExpr         -- &s
  | PField ValExpr String  -- s.q
s = Var "s" ; f = "f" ; p = Ptr "p" ; q = "q"
starp = DeRef p
sf = VField s f
amps = AddrOf s
sq = PField s q
\end{code}
Syntactic equivalences:
\begin{eqnarray*}
   *s.q    &\equiv& *(s.q)
\\ p \to f &\equiv& (*p).f
\end{eqnarray*}
\begin{code}
ptr2field :: PtrExpr -> String -> ValExpr
ptr2field p f = VField (DeRef p) f
\end{code}

Pretty Printing
\begin{code}
instance Show ValExpr where
  show (Var s) = s
  show (DeRef p) = "*(" ++ show p ++ ")"
  show (VField (DeRef p) f) = show p ++ " -> " ++ f
  show (VField s f) = show s ++ "." ++ f

instance Show PtrExpr where
  show (Ptr p) = p
  --show (AddrOf (VField (DeRef p) f)) = "(&"++show p++" -> "++f++")"
  show (AddrOf s) = "&("++ show s++")"
  show (PField s q) = show s ++ "." ++ q
\end{code}

Sometimes we want to observe without the arrow notation,
and explicit parentheses:
\begin{code}
vobs :: ValExpr -> String
vobs (Var s) = s
vobs (DeRef p) = "(*" ++ pobs p ++ ")"
vobs (VField s f) = vobs s ++ "." ++ f

pobs :: PtrExpr -> String
pobs (Ptr p) = p
pobs (AddrOf s) = "(&"++ vobs s++")"
pobs (PField s q) = vobs s ++ "." ++ q
\end{code}

\subsubsection{C Pointer Laws}

Key pointer law:
\begin{eqnarray*}
   \&s = p &\equiv& *p = s
\end{eqnarray*}

We start with one-shot simplifiers.

Simplification (Values)
\begin{eqnarray*}
\\ *(\&s) &=& s
\end{eqnarray*}
\begin{code}
vsimp :: Monad m => ValExpr -> m ValExpr
vsimp (DeRef (AddrOf v)) = return v
vsimp _ = fail "vsimp: not `*(&s)`"
\end{code}

Simplifications (Pointers)

Here we used $u$ when it is the only field in $s$
\begin{eqnarray*}
   \&(*p)    &   =  & p
\\ \&(s.u)   &   =  & \&s
\end{eqnarray*}
\begin{code}
psimp :: Monad m => [FieldName] -> PtrExpr -> m PtrExpr
psimp _   (AddrOf (DeRef p))     = return p
psimp ufs (AddrOf (VField s u))
 | u `elem` ufs                  =  return $ AddrOf s
psimp _   _                      =  fail "psimp: not `&(*p)` or `&(s.u)`"
\end{code}


Arrow Notation:
\begin{eqnarray*}
   \&p \to f &\equiv& \&(p \to f)
\\           &   =  & \&((*p). f)
\\ \&p \to u &   =  & \&((*p).u)
\\           &   =  & \&(*p)
\\           &   =  & p
\end{eqnarray*}

\subsubsection{Pointer Simplification}

We have a common pattern of simplifying a single potentially composite
sub-component, before simplifying at the (current) top-level.
\begin{code}
simp2 top subc subsimp subrepl topsimp
 = let top' = subrepl $ subsimp subc
   in case topsimp top' of
        Nothing     ->  top'
        Just top''  ->  top''
\end{code}

\begin{code}
psimplify :: [FieldName] -> PtrExpr -> PtrExpr
psimplify ufs ptr@(AddrOf s)
 = simp2 ptr s (vsimplify ufs) AddrOf (psimp ufs)
psimplify ufs ptr@(PField s q)
 = simp2 ptr s (vsimplify ufs) (flip PField q) (psimp ufs)
psimplify _ p = p
\end{code}

\begin{code}
vsimplify :: [FieldName] -> ValExpr -> ValExpr
vsimplify ufs val@(DeRef p)
 = simp2 val p (psimplify ufs) DeRef vsimp
vsimplify ufs val@(VField s f)
 = simp2 val s (vsimplify ufs)  (flip VField f) vsimp
vsimplify _ v = v
\end{code}


\subsubsection{Pointer Examples}

From Wait Acquisition Example:
\begin{nicec}
&(&(&(&the_thread->Wait.Lock.Default)->Lock)->Ticket_lock)->next_ticket
\end{nicec}
We can describe this in Haskell by:
\begin{code}
t = Ptr "the_thread"
fW = "Wait" ; fL = "Lock" ; fD = "Default"; fnt = "next_ticket"
fLu = "Lock1" ; fTLu = "Ticket_Lock" ; uniqueFs = [fLu,fTLu]
str1 = VField (VField (ptr2field t fW) fL) fD
ptr1 = AddrOf str1
str2 = ptr2field ptr1 fLu
ptr2 = AddrOf str2
str3 = ptr2field ptr2 fTLu
ptr3 = AddrOf str3
str4 = ptr2field ptr3 fnt
ptr4 = AddrOf str4
\end{code}
Running this:
\begin{nicec}
*CPointers> ptr4
&(&(&(&(the_thread -> Wait.Lock.Default) -> Lock1) -> Ticket_Lock) -> next_ticket)
*CPointers> psimplify uniqueFs ptr4
&(the_thread -> Wait.Lock.Default.next_ticket)
\end{nicec}
