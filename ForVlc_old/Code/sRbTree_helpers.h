
/******************************************************************************\
                          REPRÉSENTE UN ARBRE ROUGE-NOIRE

  Auteur    : David Fischer
  Intégration VLC : Rossier Jérémie (2011)
  Contact   : david.fischer.ch@gmail.com / david.fischer@hesge.ch
              jeremie.rossier@gmail.com

  Projet     : Implémentation SMPTE 2022 de VLC
  Date début : 02.05.2008
  Employeur  : Ecole d'Ingénieurs de Genève
               Laboratoire de Télécommunications
\******************************************************************************/

/* Copyright (c) 2009 David Fischer (david.fischer.ch@gmail.com)

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Retrieved from:
  https://sourceforge.net/projects/smpte2022lib/

Based on: http://en.literateprograms.org/
          Red-black_tree_(C)?action=history&offset=20080731190038
*/

// =============================================================================

sRbNode* GrandParent (const sRbNode* n)
{
  if (n == NULL)
    return NULL;
  if (n->parent == NULL) //Not the root node
    return NULL;
  if (n->parent->parent == NULL) //Not child of root
    return NULL;
  return n->parent->parent;
}

sRbNode* Sibling (const sRbNode* n)
{
  if (n == NULL)
    return NULL;
  if (n->parent == NULL) //Root node has no sibling
    return NULL;
  if (n == n->parent->left)
    return n->parent->right;
  return n->parent->left;
}

sRbNode* Uncle (const sRbNode* n)
{
  if (n == NULL)
    return NULL;
  if (n->parent == NULL) //Root node has no uncle
    return NULL;
  if (n->parent->parent == NULL) //Children of root have no uncle
    return NULL;
  return Sibling (n->parent);
}

enum sRbColor NodeColor (const sRbNode* n)
{
  return n == 0 ? BLACK : n->color;
}

sRbNode* MaximumNode (sRbNode* n)
{
  if (n == NULL)
    return NULL;
  while  (n->right) n = n->right;
  return  n;
}

// =============================================================================

void ReplaceNode (sRbTree* t, sRbNode* pOldNode, sRbNode* pNewNode);
void RotateLeft  (sRbTree* t, sRbNode* n);
void RotateRight (sRbTree* t, sRbNode* n);

sRbNode* LookupNode (const sRbTree* t, uint32_t key)
{
  sRbNode* n = t->root;

  while (n)
  {
    if      (key == n->key)
      return n;
    else if (key <  n->key)
      n = n->left;
    else
      n = n->right;
  }
  return n;
}

void ReplaceNode (sRbTree* t, sRbNode* pOldNode, sRbNode* pNewNode)
{
  if (pOldNode->parent == NULL)
  {
    t->root = pNewNode;
  }
  else
  {
    if (pOldNode == pOldNode->parent->left)
    {
      pOldNode->parent->left = pNewNode;
    }
    else
    {
      pOldNode->parent->right = pNewNode;
    }
  }

  if (pNewNode != NULL)
  {
    pNewNode->parent = pOldNode->parent;
  }
}

void RotateLeft (sRbTree* t, sRbNode* n)
{
  sRbNode* r = n->right;

  ReplaceNode (t, n, r);

  n->right = r->left;

  if (r->left != NULL) r->left->parent = n;

  r->left   = n;
  n->parent = r;
}

void RotateRight (sRbTree* t, sRbNode* n)
{
  sRbNode* L = n->left;

  ReplaceNode (t, n, L);

  n->left = L->right;

  if (L->right != NULL) L->right->parent = n;

  L->right  = n;
  n->parent = L;
}

// =============================================================================

void InsertCase2 (sRbTree* t, sRbNode* n);
void InsertCase3 (sRbTree* t, sRbNode* n);
void InsertCase4 (sRbTree* t, sRbNode* n);
void InsertCase5 (sRbTree* t, sRbNode* n);

sRbNode* NewNode
  (uint32_t pKey, void* pValue,
   enum sRbColor pColor, sRbNode* pLeft, sRbNode* pRight)
{
  sRbNode* _node = malloc (sizeof (struct sRbNode));
  if (_node == NULL) // Allocation ratée ?
    return NULL; 

  _node->key   = pKey;
  _node->value = pValue;
  _node->color = pColor;
  _node->left  = pLeft;
  _node->right = pRight;

  if (pLeft  != NULL) pLeft ->parent = _node;
  if (pRight != NULL) pRight->parent = _node;

  _node->parent = NULL;

  return _node;
}

void InsertCase1 (sRbTree* t, sRbNode* n)
{
  if (n->parent)
  {
    InsertCase2 (t, n);
  }
  else
  {
    n->color = BLACK;
  }
}

void InsertCase2 (sRbTree* t, sRbNode* n)
{
  if (NodeColor (n->parent) == BLACK)
  {
    return; // Tree is still valid
  }
  else
  {
    InsertCase3 (t, n);
  }
}

void InsertCase3 (sRbTree* t, sRbNode* n)
{
  if (NodeColor (Uncle(n)) == RED)
  {
    n->parent      ->color = BLACK;
    Uncle       (n)->color = BLACK;
    GrandParent (n)->color = RED;
    InsertCase1 (t, GrandParent (n));
  }
  else InsertCase4 (t, n);
}

void InsertCase4 (sRbTree* t, sRbNode* n)
{
  if (n == n->parent->right && n->parent == GrandParent (n)->left)
  {
    RotateLeft (t, n->parent);
    n = n->left;
  }
  else if (n == n->parent->left && n->parent == GrandParent (n)->right)
  {
    RotateRight (t, n->parent);
    n = n->right;
  }

  InsertCase5 (t, n);
}

void InsertCase5 (sRbTree* t, sRbNode* n)
{
  n->parent      ->color = BLACK;
  GrandParent (n)->color = RED;

  if (n == n->parent->left && n->parent == GrandParent (n)->left)
  {
    RotateRight (t, GrandParent (n));
  }
  else
  {
    if ( !(n == n->parent->right && n->parent == GrandParent(n)->right) )
      return; //Undefined message
    RotateLeft (t, GrandParent (n));
  }
}

// =============================================================================

void DeleteCase2 (sRbTree* t, sRbNode* n);
void DeleteCase3 (sRbTree* t, sRbNode* n);
void DeleteCase4 (sRbTree* t, sRbNode* n);
void DeleteCase5 (sRbTree* t, sRbNode* n);
void DeleteCase6 (sRbTree* t, sRbNode* n);

void DeleteCase1 (sRbTree* t, sRbNode* n)
{
  if (n->parent == NULL) return;

  DeleteCase2 (t, n);
}

void DeleteCase2 (sRbTree* t, sRbNode* n)
{
  if (NodeColor (Sibling (n)) == RED)
  {
    n->parent  ->color = RED;
    Sibling (n)->color = BLACK;

    if (n == n->parent->left)
         RotateLeft  (t, n->parent);
    else RotateRight (t, n->parent);
  }

  DeleteCase3 (t, n);
}

void DeleteCase3 (sRbTree* t, sRbNode* n)
{
  if (NodeColor (n->parent)          == BLACK &&
      NodeColor (Sibling (n))        == BLACK &&
      NodeColor (Sibling (n)->left)  == BLACK &&
      NodeColor (Sibling (n)->right) == BLACK)
  {
    Sibling (n)->color = RED;
    DeleteCase1 (t, n->parent);
  }
  else DeleteCase4 (t, n);
}

void DeleteCase4 (sRbTree* t, sRbNode* n)
{
  if (NodeColor (n->parent)          == RED   &&
      NodeColor (Sibling (n))        == BLACK &&
      NodeColor (Sibling (n)->left)  == BLACK &&
      NodeColor (Sibling (n)->right) == BLACK)
  {
    Sibling (n)->color = RED;
    n->parent  ->color = BLACK;
  }
  else DeleteCase5 (t, n);
}

void DeleteCase5 (sRbTree* t, sRbNode* n)
{
  if (n == n->parent->left &&
      NodeColor (Sibling (n))        == BLACK &&
      NodeColor (Sibling (n)->left)  == RED   &&
      NodeColor (Sibling (n)->right) == BLACK)
  {
    Sibling (n)      ->color = RED;
    Sibling (n)->left->color = BLACK;
    RotateRight (t, Sibling (n));
  }
  else if (n == n->parent->right &&
           NodeColor (Sibling (n))        == BLACK &&
           NodeColor (Sibling (n)->right) == RED   &&
           NodeColor (Sibling (n)->left)  == BLACK)
  {
    Sibling (n)       ->color = RED;
    Sibling (n)->right->color = BLACK;
    RotateLeft (t, Sibling (n));
  }

  DeleteCase6 (t, n);
}

void DeleteCase6 (sRbTree* t, sRbNode* n)
{
  Sibling (n)->color = NodeColor (n->parent);
  n->parent  ->color = BLACK;

  if (n == n->parent->left)
  {
    if ( (!NodeColor (Sibling (n)->right) == RED) ) //Node must be RED
      return;

    Sibling (n)->right->color = BLACK;
    RotateLeft (t, n->parent);
  }
  else
  {
    if ( (!NodeColor (Sibling (n)->left) == RED) ) //Node must be RED
      return;

    Sibling (n)->left->color = BLACK;
    RotateRight (t, n->parent);
  }
}

// =============================================================================

void sRbTree_ReleaseHelper (sRbTree* t, sRbNode* n)
{
  if (n == 0) return;

  if (n->left)  sRbTree_ReleaseHelper (t, n->left);
  if (n->right) sRbTree_ReleaseHelper (t, n->right);

  if (t->releaseFunc) t->releaseFunc (n->key, n->value);

  free (n);
}
